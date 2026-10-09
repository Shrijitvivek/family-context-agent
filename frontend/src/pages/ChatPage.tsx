import { useState } from "react";
import {
  Bot,
  Sparkles,
  ShieldCheck,
  MessageCircle,
  FileText,
  AlertCircle,
  UsersRound,
  User,
} from "lucide-react";

import PageHeader from "../components/ui/PageHeader";
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

  const { messages, loading, historyLoading, error, sendChatMessage } =
    useChat(familyId, selectedMemberId);

  const hasMessages = messages.length > 0;

  return (
    <main className="mx-auto flex h-[calc(100dvh-2rem)] min-h-0 w-full max-w-6xl flex-col overflow-hidden px-4 py-4 sm:px-6 lg:px-8">
      {/* Compact page header */}
      <div className="shrink-0">
        <PageHeader
          title="Family Chat"
          description="Ask questions and get help with your family's information."
        />
      </div>

      {/* Chat workspace */}
      <section className="mt-4 flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-sm">
        {/* Chat header */}
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-100 px-4 py-3 sm:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-50/70 text-violet-600 ring-1 ring-inset ring-violet-100/70">
              <Bot size={21} aria-hidden="true" />
            </div>

            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-slate-900">
                Family Assistant
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                {selectedMemberId
                  ? "Chatting with selected member context"
                  : "Chatting with whole family context"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Member context indicator */}
            {selectedMemberId && (
              <span className="hidden items-center gap-1.5 rounded-full border border-violet-100 bg-violet-50/70 px-2.5 py-1 text-xs font-medium text-violet-700 sm:inline-flex">
                <User size={12} aria-hidden="true" />
                <span>Member filtered</span>
              </span>
            )}

            {/* Family selection indicator */}
            <span
              className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-xs font-medium ${
                selectedFamilyId
                  ? "border-emerald-100 bg-emerald-50/70 text-emerald-700"
                  : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  selectedFamilyId ? "bg-emerald-500" : "bg-slate-400"
                }`}
              />
              <span className="hidden sm:inline">
                {selectedFamilyId ? "Family selected" : "No family selected"}
              </span>
              <span className="sm:hidden">
                {selectedFamilyId ? "Selected" : "None"}
              </span>
            </span>
          </div>
        </div>

        {/* Scrollable conversation area */}
        <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-slate-50/40">
          {/* History loading indicator */}
          {historyLoading && (
            <div
              className="flex min-h-0 flex-1 items-center justify-center text-sm text-slate-500"
              role="status"
            >
              Loading your conversation...
            </div>
          )}

          {/* Empty state when no messages exist */}
          {!hasMessages &&
            !loading &&
            !historyLoading &&
            !error &&
            selectedFamilyId && (
              <div className="flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-4 text-center sm:px-8">
                <div className="relative mb-4 shrink-0">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-violet-100 bg-white text-violet-600 shadow-sm sm:h-14 sm:w-14">
                    <Sparkles size={25} aria-hidden="true" />
                  </div>

                  <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm">
                    <MessageCircle size={12} aria-hidden="true" />
                  </span>
                </div>

                <h3 className="text-lg font-semibold tracking-tight text-slate-900 sm:text-xl">
                  How can I help your family?
                </h3>

                <p className="mt-2 max-w-md text-sm leading-5 text-slate-500">
                  Ask about family documents, household expenses, upcoming
                  commitments, or information available to your assistant.
                </p>

                {/* Example prompts */}
                <div className="mt-5 grid w-full max-w-xl shrink-0 gap-2.5 sm:grid-cols-2">
                  <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 text-left transition-colors hover:border-violet-200">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-violet-50/70 text-violet-600">
                      <FileText size={16} aria-hidden="true" />
                    </div>

                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800">
                        Family documents
                      </p>
                      <p className="mt-0.5 text-xs leading-4 text-slate-500">
                        Find information in uploaded documents.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 text-left transition-colors hover:border-violet-200">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                      <UsersRound size={16} aria-hidden="true" />
                    </div>

                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800">
                        Household overview
                      </p>
                      <p className="mt-0.5 text-xs leading-4 text-slate-500">
                        Explore your family's information.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

          {/* Unselected family state */}
          {!selectedFamilyId && !loading && !historyLoading && (
            <div className="flex min-h-0 flex-1 flex-col items-center justify-center px-5 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
                <UsersRound size={23} aria-hidden="true" />
              </div>

              <h3 className="mt-4 text-base font-semibold text-slate-900">
                Select a family to get started
              </h3>

              <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
                Choose a family from the sidebar to start chatting with your
                Family Assistant.
              </p>
            </div>
          )}

          {/* Messages list */}
          <div
            className={`min-h-0 flex-1 overflow-y-auto p-3 sm:p-5 ${
              (!hasMessages && !loading && !error && selectedFamilyId) ||
              historyLoading
                ? "hidden"
                : ""
            }`}
          >
            <MessageList messages={messages} />
          </div>

          {/* Error message */}
          {error && (
            <div
              role="alert"
              className="mx-3 mb-2 flex shrink-0 items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50/80 p-3 sm:mx-5"
            >
              <AlertCircle
                size={17}
                className="mt-0.5 shrink-0 text-rose-600"
                aria-hidden="true"
              />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-rose-800">
                  Something went wrong
                </p>
                <p className="mt-1 break-words text-sm leading-5 text-rose-700">
                  {error}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Fixed composer section */}
        <div className="shrink-0 border-t border-slate-200/80 bg-white px-3 pb-2 pt-3 sm:px-5 sm:pb-3">
          <ChatComposer
            onSend={(message) =>
              sendChatMessage(message, attachedDocument?.id)
            }
            familyId={familyId}
            onDocumentUpload={setAttachedDocument}
            loading={loading || historyLoading || !selectedFamilyId}
          />

          <div className="mt-2 flex items-center justify-center gap-1.5 text-center text-[10px] leading-4 text-slate-400 sm:text-[11px]">
            <ShieldCheck size={12} aria-hidden="true" />
            <span>
              Responses are based on information available to your family
              assistant.
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}