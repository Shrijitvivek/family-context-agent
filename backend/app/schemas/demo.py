"""Demo scenario file format and API shapes."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import CommitmentStatus, CommitmentType, Priority


class ScenarioFamily(BaseModel):
    name: str
    timezone: str = "Asia/Kolkata"


class ScenarioMember(BaseModel):
    key: str
    name: str
    relationship_type: str = "OTHER"
    display_role: str | None = None


class ScenarioCommitment(BaseModel):
    key: str
    member: str | None = None
    commitment_type: CommitmentType
    category: str = "GENERAL"
    title: str
    description: str | None = None
    amount: Decimal | None = None
    due_in_days: int | None = None
    status: CommitmentStatus = CommitmentStatus.PENDING
    priority: Priority = Priority.MEDIUM


class ScenarioDependency(BaseModel):
    source: str
    target: str


class ScenarioExpense(BaseModel):
    member: str | None = None
    amount: Decimal = Field(gt=0)
    category: str
    merchant: str | None = None
    description: str | None = None
    days_ago: int = Field(default=0, ge=0)


class Scenario(BaseModel):
    """A versioned, fictional household. Dates are offsets from the load day."""

    id: str
    title: str
    description: str = ""
    family: ScenarioFamily
    members: list[ScenarioMember] = Field(default_factory=list)
    commitments: list[ScenarioCommitment] = Field(default_factory=list)
    dependencies: list[ScenarioDependency] = Field(default_factory=list)
    expenses: list[ScenarioExpense] = Field(default_factory=list)


class ScenarioSummary(BaseModel):
    id: str
    title: str
    description: str


class DemoLoadResult(BaseModel):
    scenario_id: str
    family_id: UUID
    members: int
    commitments: int
    dependencies: int
    expenses: int
    attention_items: int
