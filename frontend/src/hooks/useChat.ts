
import { useCallback, useEffect, useState } from "react";

import {
  getChatHistory,
  sendMessage,
} from "../services/api/chat";
import type { ChatMessage } from "../components/chat/MessageList";

const getStorageKey = (
  familyId: string,
  memberId: string | null,
) =>
  `family-chat:${familyId}:${memberId ?? "all-family"}`;

export function useChat(
  familyId: string,
  memberId: string | null,
) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Restore the correct conversation when the family or member changes.
  useEffect(() => {
    let cancelled = false;

    setMessages([]);
    setConversationId(undefined);
    setError(null);

    if (!familyId) {
      setHistoryLoading(false);
      return;
    }

    const storageKey = getStorageKey(familyId, memberId);

    const restoreConversation = async () => {
      const savedConversationId = localStorage.getItem(storageKey);

      if (!savedConversationId) {
        if (!cancelled) {
          setHistoryLoading(false);
        }
        return;
      }

      setHistoryLoading(true);

      try {
        const history = await getChatHistory(
          savedConversationId,
          familyId,
        );

        if (cancelled) return;

        setConversationId(history.conversation_id);
        setMessages(
          history.messages.map((message) => ({
            id: message.id,
            role: message.role,
            content: message.content,
          })),
        );
      } catch {
        if (!cancelled) {
          setError("Unable to load your previous conversation.");
        }
      } finally {
        if (!cancelled) {
          setHistoryLoading(false);
        }
      }
    };

    void restoreConversation();

    return () => {
      cancelled = true;
    };
  }, [familyId, memberId]);

  const sendChatMessage = useCallback(
    async (message: string, documentId?: string) => {
      if (
        !familyId ||
        !message.trim() ||
        loading ||
        historyLoading
      ) {
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
          ...(memberId ? { member_id: memberId } : {}),
          ...(conversationId
            ? { conversation_id: conversationId }
            : {}),
          message,
          ...(documentId ? { document_id: documentId } : {}),
        });

        const nextConversationId =
          response.conversation_id ?? conversationId;

        if (nextConversationId) {
          setConversationId(nextConversationId);

          localStorage.setItem(
            getStorageKey(familyId, memberId),
            nextConversationId,
          );
        }

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
    },
    [
      familyId,
      memberId,
      conversationId,
      loading,
      historyLoading,
    ],
  );

  return {
    messages,
    conversationId,
    loading,
    historyLoading,
    error,
    sendChatMessage,
  };
}
