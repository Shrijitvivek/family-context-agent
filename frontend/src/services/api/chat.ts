import { apiClient } from "./client";

// Message sent to the Family Context Agent
export interface ChatRequest {
  family_id: string;
  user_id?: string;
  conversation_id?: string;
  message: string;
}

// Response from the Family Context Agent
export interface ChatResponse {
  message: string | null;
  conversation_id: string | null;
  tool_calls: Array<{
    name: string;
    arguments: Record<string, unknown>;
  }>;
  requires_clarification: boolean;
  metadata: Record<string, unknown>;
}

// Send a message to the Family Context Agent
export const sendMessage = async (
  data: ChatRequest
): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>("/chat", data);
  return response.data;
};