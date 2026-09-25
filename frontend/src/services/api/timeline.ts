import type { TimelineResponse } from "../../types/api";
import { apiClient } from "./client";

export async function getTimeline(): Promise<TimelineResponse> {
  const response = await apiClient.get<TimelineResponse>("/timeline");
  return response.data;
}