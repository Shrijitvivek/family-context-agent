import { apiClient } from "./client";

export interface DocumentResponse {
  document_id: string;
  filename: string;
  status: string;
}

export const getDocuments = async (): Promise<DocumentResponse[]> => {
  const response = await apiClient.get("/documents");
  return response.data.documents ?? response.data;
};