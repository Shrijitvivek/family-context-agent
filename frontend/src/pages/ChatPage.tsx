
import { useState } from "react";

import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import MessageList from "../components/chat/MessageList";
import ChatComposer from "../components/chat/ChatComposer";
import { useChat } from "../hooks/useChat";
import { useFamily } from "../context/FamilyContext";
import type { DocumentResponse } from "../services/api/documents";

export default function ChatPage() {
  const { selectedFamilyId, selectedMemberId } = useFamily();

  const [attachedDocument, setAttachedDocument] =
    useState<DocumentResponse | null>(null);

  const familyId = selectedFamilyId ?? "";

  const {
    messages,
    loading,
    historyLoading,
    error,
    sendChatMessage,
  } = useChat(familyId, selectedMemberId);

  return (
    <div>
      <PageHeader
        title="Family Chat"
        description="Ask questions and get help with your family's information."
      />

      <Card className="p-3 sm:p-4">
        <div className="mb-4 px-2 sm:px-4">
          <p className="text-sm text-gray-500">
            {selectedMemberId
              ? "Chatting with your selected family member's context."
              : "Chatting with the context of your whole family."}
          </p>
        </div>

        <div className="flex min-h-[calc(100vh-340px)] flex-col">
          <div className="flex-1 overflow-y-auto p-2 sm:p-4">
            {historyLoading ? (
              <div
                className="flex min-h-[200px] items-center justify-center text-sm text-gray-500"
                role="status"
              >
                Loading your conversation...
              </div>
            ) : (
              <MessageList messages={messages} />
            )}
          </div>

          {error && (
            <div
              role="alert"
              className="mx-2 mb-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 sm:mx-4"
            >
              {error}
            </div>
          )}

          <div className="mt-3">
            <ChatComposer
              onSend={(message) =>
                sendChatMessage(message, attachedDocument?.id)
              }
              familyId={familyId}
              onDocumentUpload={setAttachedDocument}
              loading={
                loading ||
                historyLoading ||
                !selectedFamilyId
              }
            />
          </div>
        </div>
      </Card>
    </div>
  );
}
