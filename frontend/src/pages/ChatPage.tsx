/**
 * ChatPage.tsx
 *
 * Full-height chat workspace. Fits perfectly inside the main content area
 * beside the sidebar with a fixed bottom composer and scrollable messages.
 */

import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  Bot,
  Sparkles,
  ShieldCheck,
  MessageCircle,
  FileText,
  AlertCircle,
  UsersRound,
  User,
  Loader2,
} from "lucide-react";

import MessageList from "../components/chat/MessageList";
import ChatComposer from "../components/chat/ChatComposer";
import { useChat } from "../hooks/useChat";
import { useFamily } from "../context/FamilyContext";
import type { DocumentResponse } from "../services/api/documents";

function Surface({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`min-w-0 flex-1 flex flex-col overflow-hidden bg-white sm:rounded-2xl sm:border sm:border-slate-200/80 sm:shadow-[0_2px_8px_rgba(15,23,42,0.025)] ${className}`}
    >
      {children}
    </section>
  );
}

export default function ChatPage() {
  const { selectedFamilyId, selectedMemberId } = useFamily();

  const [attachedDocument, setAttachedDocument] =
    useState<DocumentResponse | null>(null);

  const familyId = selectedFamilyId ?? "";

  const { messages, loading, historyLoading, error, sendChatMessage } =
    useChat(familyId, selectedMemberId);

  const hasMessages = messages.length > 0;
  const messagesContainerRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to newest message
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    container.scrollTo({
      top: container.scrollHeight,
      behavior: loading ? "smooth" : "auto",
    });
  }, [messages, loading, historyLoading]);

  return (
    <main className="flex h-[calc(100vh-5rem)] w-full flex-col overflow-hidden font-sans sm:h-[calc(100vh-5rem)]">
      {/* Main Chat Workspace Surface */}
      <Surface className="relative flex flex-col h-full overflow-hidden border-none bg-white sm:bg-white/75 sm:shadow-[0_18px_60px_rgba(80,70,130,0.10)] sm:backdrop-blur-2xl">
        
        {/* Desktop Chatbot Inner Header (Restored as requested) */}
        <div className="hidden shrink-0 items-center justify-between border-b border-slate-100 bg-white/90 px-6 py-4 sm:flex sm:border-white/70 sm:bg-white/65 sm:backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-100 via-indigo-50 to-pink-100 text-violet-700 ring-1 ring-inset ring-violet-200/70">
              <Bot size={19} aria-hidden="true" />
            </div>

            <div className="min-w-0">
              <h1 className="text-base font-semibold tracking-tight text-slate-950">
                Family Assistant
              </h1>
              <p className="truncate text-xs text-slate-500">
                {selectedMemberId
                  ? "Filtered by selected family member context"
                  : "Accessing full household knowledge base"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {selectedMemberId && (
              <span className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700">
                <User size={12} aria-hidden="true" />
                Member filtered
              </span>
            )}

            <span
              className={`inline-flex shrink-0 items-center gap-1.5 rounded-xl border px-2.5 py-1 text-xs font-medium ${
                selectedFamilyId
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  selectedFamilyId ? "bg-emerald-500" : "bg-slate-400"
                }`}
              />
              <span>
                {selectedFamilyId ? "Family selected" : "No family selected"}
              </span>
            </span>
          </div>
        </div>

        {/* Scrollable Conversation Container with Gradient Background */}
        <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-[#f8f8fc]">
          {/* Ambient Soft Gradient Background */}
          <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
            <div className="absolute -left-24 -top-28 h-80 w-80 rounded-full bg-violet-300/35 blur-[90px]" />
            <div className="absolute left-[22%] -top-24 h-72 w-80 rounded-full bg-lime-200/45 blur-[95px]" />
            <div className="absolute -right-24 top-[12%] h-80 w-80 rounded-full bg-fuchsia-300/35 blur-[100px]" />
            <div className="absolute bottom-[-8rem] left-[18%] h-96 w-[34rem] rounded-full bg-amber-200/55 blur-[110px]" />
            <div className="absolute -bottom-24 -right-20 h-80 w-80 rounded-full bg-rose-300/40 blur-[100px]" />
            <div className="absolute inset-0 bg-white/25" />
          </div>

          {/* History Loading Indicator */}
          {historyLoading && (
            <div
              className="flex min-h-0 flex-1 items-center justify-center gap-2 text-xs font-medium text-slate-500"
              role="status"
            >
              <Loader2 size={16} className="animate-spin text-slate-400" />
              <span>Loading conversation...</span>
            </div>
          )}

          {/* Empty State */}
          {!hasMessages &&
            !loading &&
            !historyLoading &&
            !error &&
            selectedFamilyId && (
              <div className="relative z-[1] flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-6 text-center sm:px-8">
                <div className="relative mb-3 shrink-0">
                  <div className="flex size-12 items-center justify-center rounded-2xl border border-white/90 bg-white/80 text-violet-700 shadow-[0_8px_24px_rgba(99,102,241,0.12)] backdrop-blur-xl">
                    <Sparkles size={22} aria-hidden="true" />
                  </div>

                  <span className="absolute -right-1.5 -top-1.5 flex size-5 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-xs">
                    <MessageCircle size={11} aria-hidden="true" />
                  </span>
                </div>

                <h2 className="text-base font-semibold tracking-tight text-slate-950">
                  How can I help your family?
                </h2>

                <p className="mt-1 max-w-sm text-xs leading-relaxed text-slate-500">
                  Ask about documents, household expenses, commitments, or general family guidance.
                </p>

                {/* Example Prompts */}
                <div className="mt-5 grid w-full max-w-lg shrink-0 gap-2.5 sm:grid-cols-2">
                  <div className="flex items-start gap-3 rounded-xl border border-white/90 bg-white/75 p-3.5 text-left shadow-[0_4px_18px_rgba(51,65,85,0.05)] backdrop-blur-xl transition duration-200 hover:-translate-y-0.5 hover:border-violet-200 hover:bg-white/90">
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                      <FileText size={16} aria-hidden="true" />
                    </div>

                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-900">
                        Family Documents
                      </p>
                      <p className="mt-0.5 text-[11px] leading-normal text-slate-500">
                        Retrieve insights from uploaded files.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 rounded-xl border border-white/90 bg-white/75 p-3.5 text-left shadow-[0_4px_18px_rgba(51,65,85,0.05)] backdrop-blur-xl transition duration-200 hover:-translate-y-0.5 hover:border-violet-200 hover:bg-white/90">
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                      <UsersRound size={16} aria-hidden="true" />
                    </div>

                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-900">
                        Household Schedule
                      </p>
                      <p className="mt-0.5 text-[11px] leading-normal text-slate-500">
                        Review upcoming family commitments.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

          {/* Unselected Family State */}
          {!selectedFamilyId && !loading && !historyLoading && (
            <div className="relative z-[1] flex min-h-0 flex-1 flex-col items-center justify-center px-5 text-center">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
                <UsersRound size={20} aria-hidden="true" />
              </div>

              <h2 className="mt-3 text-sm font-semibold text-slate-900">
                Select a family to start
              </h2>

              <p className="mt-1 max-w-xs text-xs leading-relaxed text-slate-500">
                Choose a family from the sidebar to begin conversing with your assistant.
              </p>
            </div>
          )}

          {/* Messages Container */}
          <div
            ref={messagesContainerRef}
            className={`relative z-[1] min-h-0 flex-1 overflow-y-auto px-4 pb-12 pt-4 text-sm leading-relaxed sm:px-6 sm:pb-16 sm:pt-6 ${
              (!hasMessages && !loading && !error && selectedFamilyId) ||
              historyLoading
                ? "hidden"
                : ""
            }`}
          >
            <MessageList messages={messages} />

            {/* 4-Dot Animated Assistant Typing Bubble */}
            {loading && (
              <div
                className="mt-4 flex w-full justify-start"
                role="status"
                aria-label="Assistant is typing"
              >
                <div className="flex min-h-[44px] items-center gap-1.5 rounded-2xl rounded-bl-xs border border-white/80 bg-white/90 px-4 py-3 shadow-[0_4px_18px_rgba(15,23,42,0.06)] backdrop-blur-sm">
                  <span className="sr-only">Assistant is typing...</span>
                  <span className="size-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
                  <span className="size-2 rounded-full bg-violet-500 animate-bounce [animation-delay:160ms]" />
                  <span className="size-2 rounded-full bg-fuchsia-500 animate-bounce [animation-delay:320ms]" />
                  <span className="size-2 rounded-full bg-amber-500 animate-bounce [animation-delay:480ms]" />
                </div>
              </div>
            )}
          </div>

          {/* Error Banner */}
          {error && (
            <div
              role="alert"
              className="mx-3 mb-2 flex shrink-0 items-center gap-2.5 rounded-xl border border-rose-200 bg-rose-50/80 p-3 shadow-2xs sm:mx-5"
            >
              <AlertCircle
                size={16}
                className="shrink-0 text-rose-600"
                aria-hidden="true"
              />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-rose-800">
                  Something went wrong
                </p>
                <p className="truncate text-[11px] text-rose-700">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Permanently Locked Fixed Composer Bottom Section */}
        <div className="relative z-10 shrink-0 border-t border-slate-200/80 bg-white px-3 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2.5 sm:px-6 sm:pb-4 sm:pt-4">
          <ChatComposer
            onSend={(message) =>
              sendChatMessage(message, attachedDocument?.id)
            }
            familyId={familyId}
            onDocumentUpload={setAttachedDocument}
            loading={loading || historyLoading || !selectedFamilyId}
          />

          <div className="mt-1.5 flex items-center justify-center gap-1.5 text-center text-[10px] text-slate-400 sm:text-[11px]">
            <ShieldCheck size={11} aria-hidden="true" />
            <span>
              Responses are generated using your household's encrypted context.
            </span>
          </div>
        </div>
      </Surface>
    </main>
  );
}