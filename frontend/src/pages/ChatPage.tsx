import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import MessageList from "../components/chat/MessageList";
import ChatComposer from "../components/chat/ChatComposer";
import { useChat } from "../hooks/useChat";
import { useFamily } from "../context/FamilyContext";

export default function ChatPage() {
  const { selectedFamilyId } = useFamily();

  const {
    messages,
    loading,
    error,
    sendChatMessage,
  } = useChat(selectedFamilyId ?? "");

  return (
    <div>
      <PageHeader
        title="Family Chat"
        description="Ask questions and get help with your family's information."
      />

      <Card className="p-3 sm:p-4">
        <div className="flex min-h-[calc(100vh-280px)] flex-col">
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
              onSend={sendChatMessage}
              loading={loading || !selectedFamilyId}
            />
          </div>
        </div>
      </Card>
    </div>
  );
}