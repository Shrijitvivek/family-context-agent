from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Import all models so SQLAlchemy metadata contains every table.
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.expense import Expense
from app.models.commitment import Commitment
from app.models.commitment_dependency import CommitmentDependency
from app.models.document import Document
from app.models.notification import Notification
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.agent_event import AgentEvent