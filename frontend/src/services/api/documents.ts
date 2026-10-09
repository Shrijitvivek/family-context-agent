import { apiClient } from "./client";

export interface DocumentResponse {
  id: string;
  family_id: string;
  uploaded_by_member_id: string | null;
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
  memberId?: string | null,
): Promise<DocumentResponse[]> => {
  const response = await apiClient.get<DocumentResponse[]>(
    "/documents",
    {
      params: {
        family_id: familyId,
        ...(memberId ? { member_id: memberId } : {}),
      },
    },
  );

  return response.data;
};

export const uploadDocument = async (
  familyId: string,
  file: File,
  memberId?: string | null,
): Promise<DocumentResponse> => {
  const formData = new FormData();

  formData.append("family_id", familyId);
  formData.append("file", file);

  if (memberId) {
    formData.append("member_id", memberId);
  }

  const response = await apiClient.post<DocumentResponse>(
    "/documents",
    formData,
  );

  return response.data;
};
