/**
 * MessageList
 *
 * Displays the conversation messages in the Family Context chat interface.
 *
 * Responsibilities:
 * - Display user and assistant messages.
 * - Visually distinguish between message types.
 * - Keep the conversation easy to read.
 * - Show an empty state when no messages exist.
 */

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface MessageListProps {
  messages: ChatMessage[];
}

export default function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex min-h-[400px] items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white p-6 text-center">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            How can I help your family?
          </h2>

          <p className="mt-2 max-w-md text-sm text-slate-500">
            Ask about family commitments, expenses, documents, or anything
            related to your family's context.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex flex-col gap-4"
      aria-live="polite"
      aria-label="Chat messages"
    >
      {messages.map((message) => {
        const isUser = message.role === "user";

        return (
          <div
            key={message.id}
            className={`flex ${isUser ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed sm:max-w-[75%] ${
                isUser
                  ? "rounded-br-md bg-slate-900 text-white"
                  : "rounded-bl-md border border-slate-200 bg-white text-slate-800"
              }`}
            >
              {message.content}
            </div>
          </div>
        );
      })}
    </div>
  );
}