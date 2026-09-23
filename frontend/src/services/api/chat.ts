
import { apiClient } from "./client";

// Message sent by the user
export interface ChatRequest {
  conversation_id?: string;
  message: string;
}

// Response returned by the backend
export interface ChatResponse {
  conversation_id: string;
  response: string;
}

// Send a message to the backend
export const sendMessage = async (
  data: ChatRequest
): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>(
    "/chat",
    data
  );

  return response.data;
};