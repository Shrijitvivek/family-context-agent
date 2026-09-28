"""Domain errors raised by repositories and services.

The API layer can map these to stable HTTP responses, while the tool dispatcher can
surface the same structured details to the agent without leaking database errors.
"""

from typing import Any


class FamilyContextError(Exception):
    """Base error with a machine-readable code and safe details."""

    code = "family_context_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class NotFoundError(FamilyContextError):
    code = "not_found"

    def __init__(self, entity: str, identifier: object) -> None:
        super().__init__(
            f"{entity} was not found.", details={"entity": entity, "id": str(identifier)}
        )


class ScopeViolationError(FamilyContextError):
    code = "scope_violation"

    def __init__(self, entity: str, identifier: object, family_id: object) -> None:
        super().__init__(
            f"{entity} does not belong to this family.",
            details={"entity": entity, "id": str(identifier), "family_id": str(family_id)},
        )


class ConflictError(FamilyContextError):
    code = "conflict"


class DuplicateCommitmentError(ConflictError):
    code = "possible_duplicate_commitment"

    def __init__(self, candidates: list[dict[str, Any]]) -> None:
        super().__init__(
            "A likely duplicate commitment already exists; confirm it instead of creating another.",
            details={"candidates": candidates},
        )


class DuplicateDependencyError(ConflictError):
    code = "duplicate_dependency"

    def __init__(self) -> None:
        super().__init__("That dependency already exists.")


class DependencyCycleError(ConflictError):
    code = "dependency_cycle"

    def __init__(self) -> None:
        super().__init__("This dependency would create a cycle.")


class InvalidStatusTransitionError(ConflictError):
    code = "invalid_status_transition"

    def __init__(self, current_status: str, requested_status: str) -> None:
        super().__init__(
            f"Cannot change a commitment from {current_status} to {requested_status}.",
            details={"current_status": current_status, "requested_status": requested_status},
        )


class PersistenceError(FamilyContextError):
    code = "persistence_error"

    def __init__(self, operation: str) -> None:
        super().__init__(f"Could not {operation}. Please try again.")


class ToolInputValidationError(FamilyContextError):
    code = "invalid_tool_input"
