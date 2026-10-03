import { apiClient } from "./client";

export interface Family {
  id: string;
  name: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export const getFamilies = async (): Promise<Family[]> => {
  const response = await apiClient.get<Family[]>("/families");
  return response.data;
};
