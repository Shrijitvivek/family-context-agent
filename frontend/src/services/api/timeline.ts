import type { TimelineResponse } from "../../types/api";
import { apiRequest } from "./client";

export function getTimeline(): Promise<TimelineResponse> {
  return apiRequest<TimelineResponse>("/api/v1/timeline");
}