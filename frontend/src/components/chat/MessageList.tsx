/**
 * MessageList
 *
 * Displays the conversation messages in the Family Context chat interface.
 *
 * Responsibilities:
 * - Display user and assistant messages.
 * - Visually distinguish between message types.
 * - Keep the conversation easy to read.
 * - Render assistant Markdown, including GitHub-style tables.
 * - Show an empty state when no messages exist.
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
            className={`flex min-w-0 ${isUser ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`min-w-0 max-w-[85%] break-words rounded-2xl px-4 py-3 text-sm leading-relaxed sm:max-w-[75%] ${
                isUser
                  ? "rounded-br-md bg-slate-900 text-white"
                  : "rounded-bl-md border border-slate-200 bg-white text-slate-800"
              }`}
            >
              {isUser ? (
                <p className="whitespace-pre-wrap">{message.content}</p>
              ) : (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                    h1: ({ children }) => (
                      <h1 className="mb-2 text-lg font-semibold">{children}</h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="mb-2 text-base font-semibold">{children}</h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="mb-2 font-semibold">{children}</h3>
                    ),
                    ul: ({ children }) => (
                      <ul className="mb-3 list-disc space-y-1 pl-5 last:mb-0">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="mb-3 list-decimal space-y-1 pl-5 last:mb-0">
                        {children}
                      </ol>
                    ),
                    table: ({ children }) => (
                      <div className="mb-3 w-full min-w-0 max-w-full overflow-x-auto last:mb-0">
                        <table className="w-full border-collapse text-left">
                          {children}
                        </table>
                      </div>
                    ),
                    th: ({ children }) => (
                      <th className="border border-slate-300 bg-slate-50 px-3 py-2 font-semibold">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="border border-slate-300 px-3 py-2 align-top">
                        {children}
                      </td>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
