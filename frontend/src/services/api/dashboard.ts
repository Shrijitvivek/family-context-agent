
import { apiClient } from "./client";

export interface Priority {
  title: string;
  priority: string;
  reason: string;
}

export interface Commitment {
  id: string;
  family_id: string;
  member_id: string | null;
  title: string;
  amount?: number;
  due_date?: string;
  status: string;
}

export const getPriorities = async (
  familyId: string,
): Promise<Priority[]> => {
  const response = await apiClient.get("/priorities", {
    params: {
      family_id: familyId,
    },
  });

  return response.data.priorities ?? response.data;
};

export const getUpcomingCommitments = async (
  familyId: string,
  memberId?: string | null,
): Promise<Commitment[]> => {
  const response = await apiClient.get("/commitments", {
    params: {
      family_id: familyId,
      ...(memberId ? { member_id: memberId } : {}),
    },
  });

  return response.data.commitments ?? response.data;
};
