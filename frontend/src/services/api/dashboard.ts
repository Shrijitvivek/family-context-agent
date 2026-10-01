import { apiClient } from "./client";

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
  const response = await apiClient.get("/priorities");
  return response.data.priorities ?? response.data;
};

export const getUpcomingCommitments = async (): Promise<Commitment[]> => {
  const response = await apiClient.get("/commitments");
  return response.data.commitments ?? response.data;
};