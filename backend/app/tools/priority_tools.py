"""Family priority agent tools exposed to the Family Context Agent."""

from app.schemas.commitment import GetFamilyPrioritiesQuery
from app.schemas.priority import GetFamilyPrioritiesToolResult
from app.services.priority import PriorityService


async def get_family_priorities(
    service: PriorityService, query: GetFamilyPrioritiesQuery
) -> GetFamilyPrioritiesToolResult:
    """Return the same attention items (with reasons) as the Priorities screen."""
    items = await service.attention_items(query.family_id)
    return GetFamilyPrioritiesToolResult(items=items)
