import { apiClient } from "./client";

export interface ScenarioSummary {
  id: string;
  title: string;
  description: string;
}

export interface DemoLoadResult {
  scenario_id: string;
  family_id: string;
  members: number;
  commitments: number;
  dependencies: number;
  expenses: number;
  attention_items: number;
}

export const getDemoScenarios = async (): Promise<ScenarioSummary[]> => {
  const response = await apiClient.get<ScenarioSummary[]>(
    "/demo/scenarios",
  );

  return response.data;
};

export const loadDemoScenario = async (
  scenarioId: string,
): Promise<DemoLoadResult> => {
  const response = await apiClient.post<DemoLoadResult>(
    `/demo/scenarios/${scenarioId}/load`,
  );

  return response.data;
};