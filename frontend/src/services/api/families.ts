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

export interface FamilyMember {
  id: string;
  family_id: string;
  name: string;
  relationship_type: string;
  display_role: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const getFamilyMembers = async (
  familyId: string,
): Promise<FamilyMember[]> => {
  const response = await apiClient.get<FamilyMember[]>(
    `/families/${familyId}/members`,
  );
  return response.data;
};