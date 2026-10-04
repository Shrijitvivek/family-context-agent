import type { TimelineResponse } from "../../types/api";
import { apiClient } from "./client";

interface BackendTimelineCommitment {
  id: string;
  title: string;
  description?: string | null;
  due_date?: string | null;
  status: string;
  priority: string;
  member_id?: string | null;
}

interface BackendTimelineDay {
  day: string;
  commitments: BackendTimelineCommitment[];
}

interface BackendTimelineResponse {
  family_id: string;
  start_date: string | null;
  end_date: string | null;
  days: BackendTimelineDay[];
}

export async function getTimeline(
  familyId: string,
): Promise<TimelineResponse> {
  const response = await apiClient.get<BackendTimelineResponse>(
    "/timeline",
    {
      params: {
        family_id: familyId,
      },
    },
  );

  const items = response.data.days.flatMap((day) =>
    day.commitments.map((item) => ({
      id: item.id,
      title: item.title,
      description: item.description,
      dueDate: item.due_date ?? day.day,
      status: item.status.toLowerCase() as
        | "pending"
        | "completed"
        | "overdue"
        | "cancelled",
      priority: item.priority.toLowerCase() as
        | "low"
        | "medium"
        | "high"
        | "urgent",
      familyMember: null,
    })),
  );

  return {
    items,
  };
}