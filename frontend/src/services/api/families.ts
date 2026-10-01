import { apiClient } from "./client";

export interface Family {
  id: string;
  name: string;
  timezone: string;
}

export const getFamilies = async (): Promise<Family[]> => {
  const response = await apiClient.get<Family[]>("/families");
  return response.data;
};
