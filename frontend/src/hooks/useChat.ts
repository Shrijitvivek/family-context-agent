import { useState } from "react";
import { sendMessage } from "../services/api/chat";
import type { ChatMessage } from "../components/chat/MessageList";

export function useChat(
  familyId: string,
  memberId: string | null,
) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendChatMessage = async (
    message: string,
    documentId?: string,
  ) => {
    if (!message.trim() || loading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message,
    };

    setMessages((current) => [...current, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const response = await sendMessage({
        family_id: familyId,
        member_id: memberId ?? undefined,
        conversation_id: conversationId,
        message,
        document_id: documentId,
      });

      setConversationId(response.conversation_id ?? undefined);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.message ?? "",
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch {
      setError("Unable to send your message. Please try again.");
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