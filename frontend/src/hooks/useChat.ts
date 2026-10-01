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

import { useEffect, useState } from "react";
import { sendMessage } from "../services/api/chat";
import { getFamilies } from "../services/api/families";
import type { ChatMessage } from "../components/chat/MessageList";

export function useChat() {
  const [familyId, setFamilyId] = useState<string>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getFamilies()
      .then((families) => {
        if (cancelled) return;
        if (families.length === 0) {
          setError("No family is available in this database yet.");
          return;
        }
        setFamilyId(families[0].id);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Unable to load your family. Please try again.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const sendChatMessage = async (message: string) => {
    if (!message.trim() || loading) {
      return;
    }

    if (!familyId) {
      setError("Your family is still loading. Please try again shortly.");
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
        conversation_id: conversationId,
        message,
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
