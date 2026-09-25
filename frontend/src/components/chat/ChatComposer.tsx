/**
 * ChatComposer
 *
 * Provides the message input area for the Family Context chat interface.
 *
 * Responsibilities:
 * - Allow the user to type a message.
 * - Send the message when the form is submitted.
 * - Support Enter to send and Shift+Enter for a new line.
 * - Show a loading state while the message is being processed.
 */

import { useState } from "react";
import { Send } from "lucide-react";
import Button from "../ui/Button";

interface ChatComposerProps {
  onSend: (message: string) => void;
  loading?: boolean;
}

export default function ChatComposer({
  onSend,
  loading = false,
}: ChatComposerProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedMessage = message.trim();

    if (!trimmedMessage || loading) {
      return;
    }

    onSend(trimmedMessage);
    setMessage("");
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      const form = event.currentTarget.form;

      if (form) {
        form.requestSubmit();
      }
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm"
    >
      <div className="flex items-end gap-3">
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask something about your family..."
          rows={2}
          disabled={loading}
          className="min-h-[52px] flex-1 resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-2 focus:ring-slate-200 disabled:cursor-not-allowed disabled:bg-slate-50"
          aria-label="Chat message"
        />

        <Button
          type="submit"
          disabled={!message.trim() || loading}
          loading={loading}
          className="shrink-0"
        >
          {!loading && <Send size={16} />}
          {!loading && <span className="ml-2">Send</span>}
        </Button>
      </div>

      <p className="mt-2 px-1 text-xs text-slate-400">
        Press Enter to send · Shift + Enter for a new line
      </p>
    </form>
  );
}