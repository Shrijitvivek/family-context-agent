/**
 * useChat
 *
 * Manages the state and API interaction for the Family Context chat.
 *
 * Responsibilities:
 * - Store the current conversation messages.
 * - Send user messages to the chat API.
 * - Add assistant responses to the conversation.
 * - Track the loading and error states.
 * - Preserve the conversation ID returned by the backend.
 */

import { useState } from "react";
import { sendMessage } from "../services/api/chat";
import type { ChatMessage } from "../components/chat/MessageList";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendChatMessage = async (message: string) => {
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
        conversation_id: conversationId,
        message,
      });

      setConversationId(response.conversation_id);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.response,
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