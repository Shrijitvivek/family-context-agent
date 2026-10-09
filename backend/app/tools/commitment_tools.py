"""Controlled commitment tools exposed by the Family Context Agent.

Business rules that belong to the agent's tool contract live here; persistence,
scope checks, and exact-duplicate protection stay in ``CommitmentService``.

- create_commitment: date-bound types need a due date, near-duplicates are
  returned for clarification (with the fields that differ, so the agent can offer
  a correction instead), and ``document_id`` routes through document confirmation.
- update_commitment: completed/cancelled items are locked, OVERDUE is set only by
  the system, and rescheduling an overdue item to a future date reopens it.
"""

import re
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.core.config import get_settings
from app.core.constants import (
    ACTIVE_COMMITMENT_STATUSES,
    CommitmentStatus,
    CommitmentType,
    Priority,
    SourceType,
)
from app.core.exceptions import (
    ConflictError,
    DuplicateCommitmentError,
    InvalidStatusTransitionError,
    ToolInputValidationError,
)
from app.models.commitment import Commitment
from app.schemas.commitment import (
    CommitmentCreate,
    CommitmentRead,
    CommitmentUpdate,
    CreateCommitmentToolResult,
    SearchCommitmentsQuery,
    SearchCommitmentsToolResult,
    UpdateCommitmentToolResult,
)
from app.schemas.document import DocumentConfirm
from app.services.commitment import CommitmentService
from app.services.document import DocumentService
from app.utils.dates import today_in



# Types that are meaningless without a date: ask instead of saving an undated bill.
DATE_REQUIRED_TYPES = frozenset(
    {
        CommitmentType.BILL,
        CommitmentType.APPOINTMENT,
        CommitmentType.LAB_TEST,
        CommitmentType.DEADLINE,
        CommitmentType.RENEWAL,
    }
)


TERMINAL_STATUSES = frozenset(
    {
        CommitmentStatus.COMPLETED,
        CommitmentStatus.CANCELLED,
    }
)


# Two active items of the same type this close together are probably the same
# bill; next month's bill (about 30 days later) is a genuinely new item.
DUPLICATE_WINDOW_DAYS = 7


_FILLER_WORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "my",
        "our",
        "for",
        "of",
        "bill",
        "payment",
        "due",
    }
)


# Fields the document's extraction may fill when the agent did not restate them.
_DOCUMENT_FILLABLE_FIELDS = (
    "category",
    "description",
    "amount",
    "start_date",
    "due_date",
)


def _today() -> date:
    return today_in(get_settings().family_timezone)


class CreateCommitmentInput(CommitmentCreate):
    """``create_commitment`` arguments: the commitment plus agent-only controls."""

    confirmed_new: bool = Field(
        default=False,
        description=(
            "Set true only after the user confirmed this is a separate item from "
            "the similar commitments a previous call returned."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def default_document_source(cls, data: Any) -> Any:
        # The real source (PDF or IMAGE) is taken from the stored document on
        # confirmation, so the model does not have to guess it.
        if isinstance(data, dict) and data.get("document_id"):
            if data.get("source_type") in (
                None,
                SourceType.TEXT,
                SourceType.TEXT.value,
            ):
                data = {
                    **data,
                    "source_type": SourceType.PDF.value,
                }

        return data


class CreateCommitmentResult(CreateCommitmentToolResult):
    title: str
    commitment_type: CommitmentType
    amount: Decimal | None
    due_date: date | None
    document_id: UUID | None
    message: str


class SearchCommitmentsResult(SearchCommitmentsToolResult):
    count: int
    message: str


class UpdateCommitmentResult(UpdateCommitmentToolResult):
    title: str
    priority: Priority
    amount: Decimal | None
    previous_amount: Decimal | None
    due_date: date | None
    previous_status: CommitmentStatus
    previous_due_date: date | None
    changes: list[str]
    message: str


def _title_words(title: str) -> set[str]:
    words = set(re.findall(r"[a-z0-9]+", title.casefold()))
    return (words - _FILLER_WORDS) or words


def _is_similar(
    existing: Commitment,
    payload: CommitmentCreate,
) -> bool:
    if existing.category and payload.category:
        if existing.category != payload.category:
            return False

    if existing.due_date and payload.due_date:
        if abs(
            (existing.due_date - payload.due_date).days
        ) > DUPLICATE_WINDOW_DAYS:
            return False

    existing_words = _title_words(existing.title)
    new_words = _title_words(payload.title)

    # "Electricity Bill" vs "KSEB Electricity Bill":
    # one title contains the other.
    return existing_words <= new_words or new_words <= existing_words


def _differences(
    existing: Commitment,
    payload: CommitmentCreate,
) -> dict[str, dict[str, Any]]:
    pairs = {
        "title": (existing.title, payload.title),
        "amount": (existing.amount, payload.amount),
        "due_date": (existing.due_date, payload.due_date),
        "category": (existing.category, payload.category),
    }

    return {
        field: {
            "existing": str(old) if old is not None else None,
            "requested": str(new) if new is not None else None,
        }
        for field, (old, new) in pairs.items()
        if new is not None and old != new
    }


def _describe_candidate(
    existing: Commitment,
    payload: CommitmentCreate,
) -> dict[str, Any]:
    return {
        "commitment_id": str(existing.id),
        "title": existing.title,
        "amount": (
            str(existing.amount)
            if existing.amount is not None
            else None
        ),
        "due_date": (
            existing.due_date.isoformat()
            if existing.due_date
            else None
        ),
        "status": existing.status,
        "differences": _differences(existing, payload),
    }


async def _reject_similar_commitments(
    service: CommitmentService,
    payload: CommitmentCreate,
) -> None:
    """Raise a clarification-ready duplicate error for near-matching active items."""

    existing = await service.search(
        SearchCommitmentsQuery(
            family_id=payload.family_id,
            commitment_type=payload.commitment_type,
        )
    )

    candidates = [
        _describe_candidate(item, payload)
        for item in existing
        if (
            item.status in ACTIVE_COMMITMENT_STATUSES
            and _is_similar(item, payload)
        )
    ]

    if not candidates:
        return

    error = DuplicateCommitmentError(candidates)

    error.details["next_step"] = (
        "Ask the user whether this is the existing item. If they are correcting it, "
        "use update_commitment on that commitment_id (amount, due_date, priority, "
        "or status). If it is a separate item, call create_commitment again with "
        "confirmed_new=true."
    )

    raise error


def _require_due_date(
    payload: CommitmentCreate,
) -> None:
    if (
        payload.due_date is None
        and payload.commitment_type in DATE_REQUIRED_TYPES
    ):
        kind = payload.commitment_type.value.replace(
            "_",
            " ",
        ).lower()

        raise ToolInputValidationError(
            f"A {kind} needs a due date. Ask the user when "
            f"'{payload.title}' is due.",
            details={
                "tool_name": "create_commitment",
                "missing_fields": ["due_date"],
            },
        )


async def _with_document_proposal(
    documents: DocumentService,
    payload: CreateCommitmentInput,
) -> CreateCommitmentInput:
    """Fill fields the agent left empty from the extraction the user confirmed."""

    if payload.document_id is None:
        raise ToolInputValidationError(
            "A document ID is required to read the uploaded document."
        )

    document = await documents.get(
    payload.family_id,
    payload.document_id,
    )

    proposal = document.extracted_data or {}
    values = payload.model_dump()

    for field in _DOCUMENT_FILLABLE_FIELDS:
        if (
            values.get(field) is None
            and proposal.get(field) is not None
        ):
            values[field] = proposal[field]

    return CreateCommitmentInput.model_validate(values)


async def create_commitment(
    service: CommitmentService,
    payload: CreateCommitmentInput,
    documents: DocumentService | None = None,
) -> CreateCommitmentResult:
    """Create one scoped commitment, from chat text or a confirmed document."""

    if payload.document_id is not None:
        if documents is None:
            raise ToolInputValidationError(
                "Saving a commitment from an uploaded document is not available here; "
                "ask the user to confirm it on the Documents page.",
                details={
                    "tool_name": "create_commitment",
                    "document_id": str(payload.document_id),
                },
            )

        payload = await _with_document_proposal(
            documents,
            payload,
        )

    _require_due_date(payload)

    if not payload.confirmed_new:
        await _reject_similar_commitments(
            service,
            payload,
        )

    if payload.document_id is not None and documents is not None:
        # Confirmation marks the document CONFIRMED in the same transaction.
        commitment = await documents.confirm(
            payload.document_id,
            DocumentConfirm.model_validate(
                payload.model_dump(
                    include=set(DocumentConfirm.model_fields)
                )
            ),
        )

        source = "the uploaded document"

    else:
        commitment = await service.create(
            CommitmentCreate.model_validate(
                payload.model_dump(
                    exclude={"confirmed_new"}
                )
            )
        )

        source = "chat"

    due = (
        f", due {commitment.due_date.isoformat()}"
        if commitment.due_date
        else ""
    )

    return CreateCommitmentResult(
        commitment_id=commitment.id,
        status=CommitmentStatus(commitment.status),
        title=commitment.title,
        commitment_type=CommitmentType(
            commitment.commitment_type
        ),
        amount=commitment.amount,
        due_date=commitment.due_date,
        document_id=commitment.document_id,
        message=f"Saved '{commitment.title}'{due} from {source}.",
    )


async def search_commitments(
    service: CommitmentService,
    query: SearchCommitmentsQuery,
) -> SearchCommitmentsResult:
    """Find commitments matching the agent's filters."""

    results = [
        CommitmentRead.model_validate(c)
        for c in await service.search(query)
    ]

    if not results:
        message = "No matching commitments were found."

    elif len(results) == 1:
        message = "Found 1 matching commitment."

    else:
        message = (
            f"Found {len(results)} matching commitments. "
            "If the user meant one of them, ask which before changing anything."
        )

    return SearchCommitmentsResult(
        commitments=results,
        count=len(results),
        message=message,
    )


def _check_status_change(
    current: CommitmentStatus,
    requested: CommitmentStatus,
) -> None:
    if requested == CommitmentStatus.OVERDUE:
        # Overdue is derived from the due date by the priority engine.
        raise InvalidStatusTransitionError(
            current.value,
            requested.value,
        )

    if current in TERMINAL_STATUSES and requested != current:
        raise InvalidStatusTransitionError(
            current.value,
            requested.value,
        )



async def update_commitment(
    service: CommitmentService,
    payload: CommitmentUpdate,
) -> UpdateCommitmentResult:
    """Update an existing commitment."""

    # Validate that at least one update field was provided.
    if (
        payload.title is None
        and payload.status is None
        and payload.priority is None
        and payload.amount is None
        and payload.due_date is None
    ):
        raise ToolInputValidationError(
            "Nothing to update. Ask the user what should change: "
            "title, amount, status, priority, or due date.",
            details={
                "tool_name": "update_commitment",
                "missing_fields": [
                    "title",
                    "status",
                    "priority",
                    "amount",
                    "due_date",
                ],
            },
        )

    current = await service.get(
        payload.family_id,
        payload.commitment_id,
    )

    previous_status = CommitmentStatus(current.status)
    previous_amount = current.amount
    previous_due_date = current.due_date
    previous_title = current.title

    if payload.status is not None:
        _check_status_change(
            previous_status,
            payload.status,
        )

    # Detect an actual due-date change.
    rescheduled = (
        payload.due_date is not None
        and payload.due_date != previous_due_date
    )

    if rescheduled:
        if previous_status in TERMINAL_STATUSES:
            raise ConflictError(
                f"'{previous_title}' is already "
                f"{previous_status.value} "
                "and cannot be rescheduled. Create a new commitment "
                "if it is happening again.",
                details={
                    "current_status": previous_status.value,
                },
            )

        if (
        current.start_date is not None
        and payload.due_date is not None
        and payload.due_date < current.start_date):
            raise ToolInputValidationError(
                f"The new due date is before '{previous_title}' "
                f"starts on {current.start_date.isoformat()}.",
                details={
                    "tool_name": "update_commitment",
                    "errors": ["due_date before start_date"],
                },
            )

    # Preserve the existing overdue-rescheduling behavior.
    status = payload.status

    if (
        status is None
        and rescheduled
        and previous_status == CommitmentStatus.OVERDUE
        and payload.due_date >= _today()  # type: ignore[operator]
    ):
        status = CommitmentStatus.PENDING

    changes: list[str] = []

    # Title change detection.
    if (
        payload.title is not None
        and payload.title != previous_title
    ):
        changes.append(
            f"title '{previous_title}' -> '{payload.title}'"
        )

    # Status change detection.
    if status is not None and status != previous_status:
        changes.append(
            f"status {previous_status.value} -> {status.value}"
        )

    # Priority change detection.
    if (
        payload.priority is not None
        and payload.priority.value != current.priority
    ):
        changes.append(
            f"priority {current.priority} -> {payload.priority.value}"
        )

    # Amount change detection.
    if (
        payload.amount is not None
        and payload.amount != current.amount
    ):
        changes.append(
            f"amount ₹{current.amount} -> ₹{payload.amount}"
        )

    # Due-date change detection.
    if rescheduled:
        old_date = (
            previous_due_date.isoformat()
            if previous_due_date
            else "no date"
        )

        new_date = (payload.due_date.isoformat()
        if payload.due_date is not None
        else "no date")

        changes.append(
        f"due date {old_date} -> {new_date}")

    if changes:
        # Preserve all supplied fields while applying any calculated status.
        commitment = await service.update(
            payload.model_copy(
                update={"status": status}
            )
        )
    else:
        # No actual changes: avoid an unnecessary database update.
        commitment = current

    # Report the updated commitment and the changes made.
    return UpdateCommitmentResult(
        commitment_id=commitment.id,
        status=CommitmentStatus(commitment.status),
        title=commitment.title,
        priority=Priority(commitment.priority),
        amount=commitment.amount,
        previous_amount=previous_amount,
        due_date=commitment.due_date,
        previous_status=previous_status,
        previous_due_date=previous_due_date,
        changes=changes,
        message=(
            f"Updated '{commitment.title}': "
            + "; ".join(changes)
            + "."
            if changes
            else (
                f"'{previous_title}' already had those values; "
                "nothing changed."
            )
        ),
    )
