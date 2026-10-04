"""Family priority agent tools exposed to the Family Context Agent."""

from app.schemas.commitment import GetFamilyPrioritiesQuery
from app.schemas.priority import GetFamilyPrioritiesToolResult
from app.services.priority import PriorityService


class GetFamilyPrioritiesResult(GetFamilyPrioritiesToolResult):
    count: int
    message: str


async def get_family_priorities(
    service: PriorityService, query: GetFamilyPrioritiesQuery
) -> GetFamilyPrioritiesResult:
    """Return the same attention items (with reasons) as the Priorities screen."""

    items = await service.attention_items(query.family_id)
    message = (
        f"{len(items)} item{'s' if len(items) != 1 else ''} need attention."
        if items
        else "Nothing needs the family's attention right now."
    )
    return GetFamilyPrioritiesResult(items=items, count=len(items), message=message)
