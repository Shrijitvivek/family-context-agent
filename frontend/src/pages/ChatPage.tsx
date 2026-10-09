
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import MessageList from "../components/chat/MessageList";
import ChatComposer from "../components/chat/ChatComposer";
import { useChat } from "../hooks/useChat";
import { useFamily } from "../context/FamilyContext";
import type { DocumentResponse } from "../services/api/documents";
import { useState } from "react";

export default function ChatPage() {
  const {
    selectedFamilyId,
    members,
    selectedMemberId,
    setSelectedMemberId,
  } = useFamily();

  const [attachedDocument, setAttachedDocument] =
    useState<DocumentResponse | null>(null);

  const { messages, loading, error, sendChatMessage } = useChat(
    selectedFamilyId ?? "",
    selectedMemberId,
  );

  return (
    <div>
      <PageHeader
        title="Family Chat"
        description="Ask questions and get help with your family's information."
      />

      <Card className="p-3 sm:p-4">
        <div className="mb-4 px-2 sm:px-4">
          <label
            htmlFor="chat-member"
            className="mb-1 block text-sm font-medium text-gray-700"
          >
            Chatting as
          </label>

          <select
            id="chat-member"
            value={selectedMemberId ?? ""}
            onChange={(event) => setSelectedMemberId(event.target.value)}
            disabled={members.length === 0 || loading}
            className="w-full max-w-sm rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          >
            {members.filter((member) => member.is_active).map((member) => (
              <option key={member.id} value={member.id}>
                {member.name}
              </option>
            ))}
          </select>

          {members.length === 0 && (
            <p className="mt-1 text-sm text-gray-500">
              No family members available.
            </p>
          )}
        </div>

        <div className="flex min-h-[calc(100vh-340px)] flex-col">
          <div className="flex-1 overflow-y-auto p-2 sm:p-4">
            <MessageList messages={messages} />
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
              familyId={selectedFamilyId ?? ""}
              onDocumentUpload={setAttachedDocument}
              loading={
                loading || !selectedFamilyId || !selectedMemberId
              }
            />
          </div>
        </div>
      </Card>
    </div>
  );
}
