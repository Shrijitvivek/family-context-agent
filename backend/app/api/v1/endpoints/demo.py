"""Judge-mode scenario endpoints. Only ever touch the scenario's own demo household."""

from fastapi import APIRouter

from app.api.dependencies import DemoServiceDep, TodayDep
from app.schemas.demo import DemoLoadResult, ScenarioSummary

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/scenarios", response_model=list[ScenarioSummary])
async def list_scenarios(service: DemoServiceDep):
    return service.list_scenarios()


@router.post("/scenarios/{scenario_id}/load", response_model=DemoLoadResult)
async def load_scenario(scenario_id: str, service: DemoServiceDep, today: TodayDep):
    return await service.load(scenario_id, today)
