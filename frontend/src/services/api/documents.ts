import { apiClient } from "./client";

export interface DocumentResponse {
  id: string;
  family_id: string;
  file_name: string;
  file_type: string | null;
  mime_type: string | null;
  document_type: string | null;
  processing_status: string | null;
  extracted_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export const getDocuments = async (
  familyId: string,
): Promise<DocumentResponse[]> => {
  const response = await apiClient.get<DocumentResponse[]>(
    "/documents",
    {
      params: {
        family_id: familyId,
      },
    },
  );

  return response.data;
};

export const uploadDocument = async (
  familyId: string,
  file: File,
): Promise<DocumentResponse> => {
  const formData = new FormData();

  formData.append("family_id", familyId);
  formData.append("file", file);

  const response = await apiClient.post<DocumentResponse>(
    "/documents",
    formData,
  );

  return response.data;
};