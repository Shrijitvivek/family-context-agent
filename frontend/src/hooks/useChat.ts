import { useState } from "react";
import { sendMessage } from "../services/api/chat";
import type { ChatMessage } from "../components/chat/MessageList";

export function useChat(familyId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendChatMessage = async (
    message: string,
    documentId?: string,
  ) => {
    // Don't send empty messages
    if (!message.trim() || loading) {
      return;
    }

    // Add user's message immediately to the chat
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message,
    };

    setMessages((current) => [...current, userMessage]);
    setLoading(true);
    setError(null);

    try {
      console.log("Sending chat request:", {
        family_id: familyId,
        conversation_id: conversationId,
        message,
        document_id: documentId,
      });

      const response = await sendMessage({
        family_id: familyId,
        conversation_id: conversationId,
        message,
        document_id: documentId,
      });

      console.log("Chat response:", response);

      // Save conversation ID for the next message
      setConversationId(response.conversation_id ?? undefined);

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.message ?? "",
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      // Log the actual error in browser console
      console.error("CHAT REQUEST ERROR:", error);

      // Show the real error instead of hiding it
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Unable to send your message. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return {
    messages,
    loading,
    error,
    sendChatMessage,
  };
}