/**
 * ChatComposer
 *
 * Provides the message input area for the Family Context chat interface.
 */

import { useState, useRef } from "react";
import { Send, Paperclip } from "lucide-react";
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
  const [selectedFile, setSelectedFile] = useState<File | null>(null); // State to hold the selected file
  const fileInputRef = useRef<HTMLInputElement | null>(null); // Ref for the file input element

  // Handle file selection
  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>, // Add this line to specify the type of the event
  ) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
  };

  // Handle file upload
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedMessage = message.trim(); // Trim leading and trailing spaces

    if (!trimmedMessage || loading) {
      return;
    }

    onSend(trimmedMessage);
    setMessage("");
  };

  // Handle Enter key press for sending message
  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      // Check if Enter is pressed without Shift
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
      {selectedFile && (
        <div className="mb-2 flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
          <Paperclip size={14} />
          <span className="truncate">{selectedFile.name}</span>
        </div>
      )}

      <div className="flex items-end gap-3">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleFileChange}
          className="hidden"
        />

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          className="mb-1 shrink-0 rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Attach document"
        >
          <Paperclip size={23} />
        </button>

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
