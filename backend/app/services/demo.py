"""Synthetic demo scenarios for judge mode.

Each scenario owns a deterministic family id derived from its scenario id, so
loading or resetting a scenario can only ever touch that demo household.
"""

from datetime import date, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import NotFoundError, PersistenceError, ToolInputValidationError
from app.models.commitment import Commitment
from app.models.commitment_dependency import CommitmentDependency
from app.models.expense import Expense
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.repositories.family import FamilyRepository
from app.schemas.demo import DemoLoadResult, Scenario, ScenarioSummary
from app.services.priority import PriorityService

_DEMO_NAMESPACE = uuid5(NAMESPACE_URL, "family-context-agent/demo")


def demo_family_id(scenario_id: str) -> UUID:
    return uuid5(_DEMO_NAMESPACE, scenario_id)


class DemoService:
    def __init__(
        self,
        families: FamilyRepository,
        priorities: PriorityService,
        scenario_dir: Path,
    ) -> None:
        self._families = families
        self._priorities = priorities
        self._scenario_dir = scenario_dir

    def _read_all(self) -> dict[str, Scenario]:
        scenarios: dict[str, Scenario] = {}
        for path in sorted(self._scenario_dir.glob("*.json")):
            try:
                scenario = Scenario.model_validate_json(path.read_text(encoding="utf-8"))
            except ValidationError as exc:
                raise ToolInputValidationError(
                    f"Demo scenario file {path.name} is invalid.",
                    details={"errors": exc.errors(include_url=False)},
                ) from exc
            scenarios[scenario.id] = scenario
        return scenarios

    def list_scenarios(self) -> list[ScenarioSummary]:
        return [
            ScenarioSummary(id=s.id, title=s.title, description=s.description)
            for s in self._read_all().values()
        ]

    async def load(self, scenario_id: str, today: date) -> DemoLoadResult:
        """Replace the scenario's demo household in one transaction, then prioritise.

        Idempotent: loading the same scenario twice yields the same household.
        """

        scenario = self._read_all().get(scenario_id)
        if scenario is None:
            raise NotFoundError("Demo scenario", scenario_id)

        family_id = demo_family_id(scenario.id)
        family = Family(id=family_id, name=scenario.family.name, timezone=scenario.family.timezone)
        members = {
            m.key: FamilyMember(
                id=uuid4(),
                family_id=family_id,
                name=m.name,
                relationship_type=m.relationship_type,
                display_role=m.display_role,
            )
            for m in scenario.members
        }

        def member_id(key: str | None) -> UUID | None:
            if key is None:
                return None
            if key not in members:
                raise ToolInputValidationError(
                    f"Scenario {scenario.id} references unknown member '{key}'."
                )
            return members[key].id

        commitments = {
            c.key: Commitment(
                id=uuid4(),
                family_id=family_id,
                member_id=member_id(c.member),
                commitment_type=c.commitment_type.value,
                category=c.category,
                title=c.title,
                description=c.description,
                amount=c.amount,
                due_date=today + timedelta(days=c.due_in_days)
                if c.due_in_days is not None
                else None,
                status=c.status.value,
                priority=c.priority.value,
                source_type="MANUAL",
            )
            for c in scenario.commitments
        }
        try:
            dependencies = [
                CommitmentDependency(
                    family_id=family_id,
                    source_commitment_id=commitments[d.source].id,
                    target_commitment_id=commitments[d.target].id,
                )
                for d in scenario.dependencies
            ]
        except KeyError as exc:
            raise ToolInputValidationError(
                f"Scenario {scenario.id} links an unknown commitment {exc}."
            ) from exc
        expenses = [
            Expense(
                family_id=family_id,
                member_id=member_id(e.member),
                amount=e.amount,
                category=e.category,
                merchant=e.merchant,
                description=e.description,
                expense_date=today - timedelta(days=e.days_ago),
                source_type="MANUAL",
            )
            for e in scenario.expenses
        ]

        try:
            await self._families.delete_family(family_id)
            # Parents first so foreign keys resolve within the single flush order.
            await self._families.add_all([family])
            await self._families.add_all(list(members.values()))
            await self._families.add_all(list(commitments.values()))
            await self._families.add_all([*dependencies, *expenses])
            await self._families.commit()
        except SQLAlchemyError as exc:
            await self._families.rollback()
            raise PersistenceError("load the demo scenario") from exc

        recalculated = await self._priorities.recalculate(family_id, today)
        return DemoLoadResult(
            scenario_id=scenario.id,
            family_id=family_id,
            members=len(members),
            commitments=len(commitments),
            dependencies=len(dependencies),
            expenses=len(expenses),
            attention_items=recalculated.active_items,
        )
