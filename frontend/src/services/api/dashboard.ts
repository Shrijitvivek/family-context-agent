import { apiRequest } from "./client";

export interface Priority {
  title: string;
  priority: string;
  reason: string;
}

export interface Commitment {
  commitment_id: string;
  title: string;
  amount?: number;
  due_date?: string;
  status: string;
}

export const getPriorities = async (): Promise<Priority[]> => {
  const response = await apiRequest<{ priorities?: Priority[] } | Priority[]>("/api/v1/priorities");
  return Array.isArray(response) ? response : response.priorities ?? [];
};

export const getUpcomingCommitments = async (): Promise<Commitment[]> => {
  const response = await apiRequest<{ commitments?: Commitment[] } | Commitment[]>("/api/v1/commitments");
  return Array.isArray(response) ? response : response.commitments ?? [];
};