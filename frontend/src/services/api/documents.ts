import { apiRequest } from "./client";

export interface DocumentResponse {
  document_id: string;
  filename: string;
  status: string;
}

export const getDocuments = async (): Promise<DocumentResponse[]> => {
  const response = await apiRequest<{ documents?: DocumentResponse[] } | DocumentResponse[]>("/api/v1/documents");
  return Array.isArray(response) ? response : response.documents ?? [];
};