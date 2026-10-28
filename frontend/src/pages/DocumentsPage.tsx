import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, ReactNode } from "react";
import {
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Clock3,
  FileText,
  Files,
  ShieldCheck,
  Upload,
  UserRound,
  Wallet,
  X,
  RefreshCw,
} from "lucide-react";

import DocumentCard from "../components/documents/DocumentCard";
import {
  confirmDocument,
  getDocuments,
  type DocumentResponse,
  uploadDocument,
} from "../services/api/documents";
import { useFamily } from "../context/FamilyContext";
import { formatDate } from "../utils/date";

type ExtractedData = Record<string, unknown>;

type CommitmentDraft = {
  title: string;
  commitment_type: string;
  category: string;
  description: string;
  amount: string;
  start_date: string;
  due_date: string;
  member_name: string;
  member_id: string;
};

type DetailItem = { label: string; value: string };

const COMMITMENT_TYPES = [
  { value: "BILL", label: "Bill" },
  { value: "APPOINTMENT", label: "Appointment" },
  { value: "LAB_TEST", label: "Lab test" },
  { value: "HOME_TASK", label: "Home task" },
  { value: "TASK", label: "Task" },
  { value: "EDUCATION", label: "Education" },
  { value: "DEADLINE", label: "Deadline" },
  { value: "RENEWAL", label: "Renewal" },
];

const EXCLUDED_DETAIL_KEYS = new Set([
  "confidence",
  "missingfields",
  "title",
  "commitmenttitle",
  "commitmenttype",
  "category",
  "description",
  "amount",
  "startdate",
  "duedate",
  "membername",
  "appointmentdate",
  "eventdate",
  "visitdate",
  "meetingdate",
  "family",
  "familyname",
  "member",
  "memberaccount",
  "accountname",
  "documenttype",
  "type",
]);

function normalizeKey(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function normalizeFamilyName(value: string): string {
  return normalizeKey(value)
    .replace(/^the/, "")
    .replace(/family$/, "");
}

function toDisplayLabel(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function toReadableValue(value: unknown): string {
  if (value === null || value === undefined || value === "")
    return "Not available";
  if (typeof value === "string") return value.trim() || "Not available";
  if (typeof value === "number" || typeof value === "boolean")
    return String(value);
  if (Array.isArray(value)) {
    return (
      value
        .map(toReadableValue)
        .filter((item) => item !== "Not available")
        .join(", ") || "Not available"
    );
  }
  return "Not available";
}

function flattenEntries(
  data: ExtractedData,
): Array<{ key: string; value: unknown }> {
  const result: Array<{ key: string; value: unknown }> = [];
  const visit = (record: Record<string, unknown>) => {
    Object.entries(record).forEach(([key, value]) => {
      if (value && typeof value === "object" && !Array.isArray(value)) {
        visit(value as Record<string, unknown>);
      } else {
        result.push({ key, value });
      }
    });
  };
  visit(data);
  return result;
}

function findValue(data: ExtractedData, aliases: string[]): unknown {
  const wanted = new Set(aliases.map(normalizeKey));
  const entries = flattenEntries(data);
  for (const entry of entries) {
    if (
      wanted.has(normalizeKey(entry.key)) &&
      entry.value !== null &&
      entry.value !== undefined &&
      entry.value !== ""
    ) {
      return entry.value;
    }
  }
  return undefined;
}

function normalizeDate(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) return "";
  const text = value.trim();
  const isoMatch = text.match(/^(\d{4}-\d{2}-\d{2})/);
  if (isoMatch) return isoMatch[1];
  const parsed = Date.parse(text);
  if (Number.isNaN(parsed)) return "";
  const date = new Date(parsed);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function normalizeCommitmentType(
  value: unknown,
  documentType: string | null,
): string {
  const raw = typeof value === "string" ? value : (documentType ?? "");
  const normalized = raw
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
  if (COMMITMENT_TYPES.some((item) => item.value === normalized))
    return normalized;
  const lower = raw.toLowerCase();
  if (/appointment|meeting|doctor|clinic|dent(al|ist)/.test(lower))
    return "APPOINTMENT";
  if (/lab.?test|blood.?test|diagnostic/.test(lower)) return "LAB_TEST";
  if (
    /bill|invoice|fee|electricity|water|broadband|maintenance|lpg|payment/.test(
      lower,
    )
  )
    return "BILL";
  if (/renewal|renew/.test(lower)) return "RENEWAL";
  if (/education|school/.test(lower)) return "EDUCATION";
  if (/home.?task/.test(lower)) return "HOME_TASK";
  if (/deadline/.test(lower)) return "DEADLINE";
  return "TASK";
}

function titleFromFilename(fileName: string): string {
  const withoutExtension = fileName.replace(/\.[^.]+$/, "");
  const cleaned = withoutExtension
    .replace(/^\d+[_\s-]*/, "")
    .replace(/\b\d{4}-\d{2}-\d{2}\b/g, " ")
    .replace(/\b(due|judging)\b/gi, " ")
    .replace(/\b(taylor|morgan|parker|family)\b/gi, " ")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned || "Document commitment";
}

function buildDraft(
  document: DocumentResponse,
  members: Array<{ id: string; name: string }>,
  selectedMemberId: string | null,
): CommitmentDraft {
  const data = (document.extracted_data ?? {}) as ExtractedData;
  const type = normalizeCommitmentType(
    findValue(data, [
      "commitment_type",
      "commitment type",
      "document_type",
      "record_type",
      "type",
    ]),
    document.document_type,
  );
  const rawTitle = findValue(data, [
    "title",
    "commitment_title",
    "bill_title",
    "document_title",
    "appointment_title",
    "service_name",
    "fee_type",
  ]);
  const appointmentDate = findValue(data, [
    "appointment_date",
    "event_date",
    "visit_date",
    "meeting_date",
    "start_date",
    "date",
  ]);
  const dueDate = findValue(data, [
    "due_date",
    "due date",
    "payment_due_date",
    "bill_due_date",
    "deadline",
  ]);
  const rawAmount = findValue(data, [
    "amount",
    "total_amount",
    "bill_amount",
    "payable_amount",
    "fee_amount",
    "total_due",
  ]);
  const rawCategory = findValue(data, [
    "category",
    "bill_category",
    "document_category",
  ]);
  const description = findValue(data, [
    "description",
    "summary",
    "reason",
    "purpose",
    "document_details",
  ]);
  const member = findValue(data, [
    "member_name",
    "member / account",
    "member",
    "person",
    "patient",
    "student",
    "account_name",
  ]);
  const memberName = typeof member === "string" ? member.trim() : "";
  const matchedMember = memberName
    ? members.find(
        (item) => item.name.trim().toLowerCase() === memberName.toLowerCase(),
      )
    : undefined;

  let amount = "";
  if (typeof rawAmount === "number") amount = String(rawAmount);
  else if (typeof rawAmount === "string")
    amount = rawAmount.replace(/[₹,\s]/g, "").replace(/^(INR|Rs\.?)/i, "");

  const startDate = normalizeDate(appointmentDate);
  let normalizedDueDate = normalizeDate(dueDate);
  if (type === "APPOINTMENT" || type === "LAB_TEST") {
    if (!normalizedDueDate && startDate) normalizedDueDate = "";
  }

  return {
    title:
      typeof rawTitle === "string" && rawTitle.trim()
        ? rawTitle.trim()
        : titleFromFilename(document.file_name),
    commitment_type: type,
    category: typeof rawCategory === "string" ? rawCategory : "",
    description: typeof description === "string" ? description : "",
    amount,
    start_date: startDate,
    due_date: normalizedDueDate,
    member_name: memberName,
    member_id: memberName
      ? (matchedMember?.id ?? "")
      : (selectedMemberId ?? ""),
  };
}

function getAdditionalDetails(data: ExtractedData): DetailItem[] {
  const seen = new Set<string>();
  const entries = flattenEntries(data);
  const items: DetailItem[] = [];
  for (const { key, value } of entries) {
    const normalized = normalizeKey(key);
    if (EXCLUDED_DETAIL_KEYS.has(normalized) || normalized === "fields")
      continue;
    if (value === null || value === undefined || value === "") continue;
    const readable = toReadableValue(value);
    if (readable === "Not available") continue;
    const label = toDisplayLabel(key);
    const signature = `${normalizeKey(label)}:${readable.toLowerCase()}`;
    if (seen.has(signature)) continue;
    seen.add(signature);
    items.push({ label, value: readable });
  }
  return items;
}

function StatusBadge({ status }: { status: string | null }) {
  const normalized = (status ?? "UNKNOWN").toUpperCase();
  const styles: Record<string, string> = {
    NEEDS_CONFIRMATION: "border-amber-200 bg-amber-50 text-amber-800",
    CONFIRMED: "border-emerald-200 bg-emerald-50 text-emerald-700",
    PENDING: "border-blue-200 bg-blue-50 text-blue-700",
    FAILED: "border-rose-200 bg-rose-50 text-rose-700",
    UNREADABLE: "border-slate-200 bg-slate-100 text-slate-700",
  };
  return (
    <span
      className={`inline-flex max-w-full items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold leading-4 ${styles[normalized] ?? styles.UNREADABLE}`}
    >
      {normalized.replace(/_/g, " ")}
    </span>
  );
}

function Surface({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`min-w-0 rounded-2xl border border-slate-200/80 bg-white shadow-[0_2px_8px_rgba(15,23,42,0.025)] ${className}`}
    >
      {children}
    </section>
  );
}

export default function DocumentsPage() {
  const { families, members, selectedFamilyId, selectedMemberId } = useFamily();
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [selectedDocument, setSelectedDocument] =
    useState<DocumentResponse | null>(null);
  const [draft, setDraft] = useState<CommitmentDraft | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [showMoreDetails, setShowMoreDetails] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;
    const loadDocuments = async () => {
      if (!selectedFamilyId) {
        setDocuments([]);
        setLoading(false);
        setError(null);
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const data = await getDocuments(selectedFamilyId, selectedMemberId);
        if (!cancelled) setDocuments(data);
      } catch {
        if (!cancelled) setError("Unable to load documents. Please try again.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void loadDocuments();
    return () => {
      cancelled = true;
    };
  }, [selectedFamilyId, selectedMemberId, retryCount]);

  const selectedData = (selectedDocument?.extracted_data ??
    {}) as ExtractedData;
  const additionalDetails = useMemo(
    () =>
      getAdditionalDetails(
        (selectedDocument?.extracted_data ?? {}) as ExtractedData,
      ),
    [selectedDocument?.extracted_data],
  );
  const currentFamilyName =
    families.find((family) => family.id === selectedFamilyId)?.name ?? "";
  const extractedFamilyName = selectedDocument
    ? toReadableValue(
        findValue(selectedData, ["family", "family_name", "household_name"]),
      )
    : "Not available";
  const familyMismatch =
    extractedFamilyName !== "Not available" &&
    currentFamilyName &&
    normalizeFamilyName(extractedFamilyName) !==
      normalizeFamilyName(currentFamilyName);

  const openDocument = (document: DocumentResponse) => {
    setSelectedDocument(document);
    setDraft(buildDraft(document, members, selectedMemberId));
    setConfirmError("");
    setShowMoreDetails(false);
  };

  const closeDocument = () => {
    if (confirming) return;
    setSelectedDocument(null);
    setDraft(null);
    setConfirmError("");
  };

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedFamilyId) return;
    try {
      setUploading(true);
      setError(null);
      await uploadDocument(selectedFamilyId, file, selectedMemberId);
      const data = await getDocuments(selectedFamilyId, selectedMemberId);
      setDocuments(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to upload document. Please try again.",
      );
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleConfirmSelectedDocument = async () => {
    if (!selectedDocument || !selectedFamilyId || !draft) return;
    if (!draft.title.trim()) {
      setConfirmError("Please enter a title before creating the commitment.");
      return;
    }
    if (!draft.commitment_type) {
      setConfirmError("Please choose what type of commitment this is.");
      return;
    }
    const parsedAmount = draft.amount.trim()
      ? Number(draft.amount.replace(/[₹,\s]/g, ""))
      : undefined;
    if (
      parsedAmount !== undefined &&
      (!Number.isFinite(parsedAmount) || parsedAmount <= 0)
    ) {
      setConfirmError(
        "Enter a valid amount greater than zero, or leave it blank.",
      );
      return;
    }

    setConfirming(true);
    setConfirmError("");
    try {
      await confirmDocument(selectedDocument.id, {
        family_id: selectedFamilyId,
        member_id: draft.member_id || undefined,
        commitment_type: draft.commitment_type,
        title: draft.title.trim(),
        category: draft.category.trim() || undefined,
        description: draft.description.trim() || undefined,
        amount: parsedAmount,
        start_date: draft.start_date || undefined,
        due_date: draft.due_date || undefined,
      });
      const updatedDocuments = await getDocuments(
        selectedFamilyId,
        selectedMemberId,
      );
      setDocuments(updatedDocuments);
      setSelectedDocument(null);
      setDraft(null);
    } catch (err) {
      setConfirmError(
        err instanceof Error
          ? err.message
          : "Unable to confirm this document. Please try again.",
      );
    } finally {
      setConfirming(false);
    }
  };

  const updateDraft = (field: keyof CommitmentDraft, value: string) => {
    setDraft((current) => (current ? { ...current, [field]: value } : current));
  };

  const updateMember = (memberId: string) => {
    const member = members.find((item) => item.id === memberId);
    setDraft((current) =>
      current
        ? { ...current, member_id: memberId, member_name: member?.name ?? "" }
        : current,
    );
  };

  return (
    <main className="mx-auto w-full max-w-[1600px] min-w-0 space-y-4 pb-6 font-sans sm:space-y-6 sm:pb-8">
      <Surface className="flex min-w-0 flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:gap-6 sm:p-8">
        <div className="min-w-0">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50/70 px-3 py-1.5">
            <FileText aria-hidden="true" size={14} className="text-blue-600" />
            <span className="text-xs font-semibold text-blue-700">
              Family documents
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-[-0.055em] text-slate-950 sm:text-4xl">
            Documents
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-600">
            View, review and manage your family’s important documents.
          </p>
        </div>

        <label
          htmlFor="document-upload"
          className={`inline-flex w-full shrink-0 cursor-pointer items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold shadow-sm transition sm:w-auto sm:py-2.5 sm:text-xs ${
            uploading || !selectedFamilyId
              ? "cursor-not-allowed border border-slate-200 bg-slate-100 text-slate-400"
              : "bg-slate-900 text-white hover:bg-slate-800"
          }`}
        >
          {uploading ? (
            <RefreshCw size={16} className="animate-spin" aria-hidden="true" />
          ) : (
            <Upload size={16} aria-hidden="true" />
          )}
          {uploading ? "Uploading…" : "Upload document"}
          <input
            ref={fileInputRef}
            id="document-upload"
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            disabled={uploading || !selectedFamilyId}
            onChange={handleUpload}
            className="sr-only"
          />
        </label>
      </Surface>

      <Surface className="flex flex-col gap-3 bg-slate-50/50 p-4 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:p-5">
        <div className="flex items-start gap-2">
          <FileText
            size={15}
            className="mt-0.5 shrink-0 text-slate-400"
            aria-hidden="true"
          />
          <span>Supported formats: PDF, JPG, JPEG and PNG</span>
        </div>
        <div className="flex items-start gap-2">
          <ShieldCheck
            size={15}
            className="mt-0.5 shrink-0 text-emerald-600"
            aria-hidden="true"
          />
          <span>Securely stored and processed</span>
        </div>
      </Surface>

      {error && (
        <div
          role="alert"
          className="flex min-w-0 flex-col gap-3 rounded-2xl border border-rose-200 bg-rose-50/70 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5"
        >
          <div className="flex min-w-0 gap-2">
            <AlertCircle size={18} className="mt-0.5 shrink-0 text-rose-700" />
            <div>
              <p className="text-sm font-semibold text-rose-800">
                Something went wrong
              </p>
              <p className="mt-1 break-words text-sm text-rose-700">{error}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setRetryCount((count) => count + 1)}
            disabled={loading}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-rose-200 bg-white px-4 py-2.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-50 disabled:opacity-60"
          >
            <RefreshCw size={14} aria-hidden="true" />
            Try again
          </button>
        </div>
      )}

      <Surface className="min-w-0 p-4 sm:p-6">
        <div className="mb-5 flex min-w-0 flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <h2 className="text-base font-semibold tracking-tight text-slate-950">
              Your documents
            </h2>
            <p className="mt-1 text-xs leading-relaxed text-slate-500">
              Open a document to review the information extracted by Eva.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {selectedMemberId && (
              <span className="inline-flex items-center gap-1.5 rounded-xl border border-violet-100 bg-violet-50/70 px-3 py-1.5 text-xs font-medium text-violet-700">
                <UserRound size={13} aria-hidden="true" />
                Member filtered
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">
              <Files size={13} aria-hidden="true" />
              {documents.length}{" "}
              {documents.length === 1 ? "document" : "documents"}
            </span>
          </div>
        </div>

        {loading ? (
          <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-3">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="min-w-0 animate-pulse space-y-3 rounded-2xl border border-slate-200 bg-slate-50/50 p-4 sm:p-5"
              >
                <div className="h-10 w-10 rounded-xl bg-slate-200" />
                <div className="h-4 w-3/4 rounded bg-slate-200" />
                <div className="h-3 w-1/2 rounded bg-slate-200" />
              </div>
            ))}
          </div>
        ) : !selectedFamilyId ? (
          <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center sm:py-12">
            <Files
              size={24}
              className="mx-auto text-slate-400"
              aria-hidden="true"
            />
            <h3 className="mt-3 text-sm font-semibold text-slate-900">
              Select a family
            </h3>
            <p className="mx-auto mt-1 max-w-sm text-xs leading-relaxed text-slate-500">
              Choose a family to view and manage its documents.
            </p>
          </div>
        ) : documents.length === 0 && !error ? (
          <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center sm:py-12">
            <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
              <FileText size={22} aria-hidden="true" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900">
              No documents yet
            </h3>
            <p className="mx-auto mt-1 max-w-sm text-xs leading-relaxed text-slate-500">
              Upload your first family document using the button above. Your
              uploaded files will appear here.
            </p>
          </div>
        ) : (
          <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-3">
            {documents.map((document) => (
              <button
                key={document.id}
                type="button"
                onClick={() => openDocument(document)}
                className="w-full min-w-0 rounded-2xl text-left transition hover:-translate-y-0.5 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                aria-label={`View details for ${document.file_name}`}
              >
                <DocumentCard
                  filename={document.file_name}
                  status={document.processing_status ?? "UNKNOWN"}
                />
              </button>
            ))}
          </div>
        )}
      </Surface>

      {selectedDocument && draft && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/45 p-0 backdrop-blur-[2px] sm:items-center sm:p-4"
          onClick={closeDocument}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-details-title"
            className="flex max-h-[94dvh] w-full min-w-0 max-w-2xl flex-col overflow-hidden rounded-t-3xl bg-white shadow-2xl sm:max-h-[min(90vh,800px)] sm:rounded-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="flex shrink-0 items-start gap-3 border-b border-slate-100 px-4 py-4 sm:px-6 sm:py-5">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-700">
                <FileText size={20} aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <h2
                  id="document-details-title"
                  className="text-base font-semibold text-slate-950 sm:text-lg"
                >
                  Review document
                </h2>
                <p className="mt-1 break-words text-xs leading-relaxed text-slate-500 sm:text-sm">
                  {selectedDocument.file_name}
                </p>
                <div className="mt-2">
                  <StatusBadge status={selectedDocument.processing_status} />
                </div>
              </div>
              <button
                type="button"
                onClick={closeDocument}
                disabled={confirming}
                aria-label="Close document details"
                className="inline-flex size-9 shrink-0 items-center justify-center rounded-xl text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 disabled:opacity-50"
              >
                <X size={19} aria-hidden="true" />
              </button>
            </header>

            <div className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain px-4 py-4 sm:space-y-6 sm:px-6 sm:py-5">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div className="flex min-w-0 items-start gap-2 rounded-xl border border-slate-200 p-3">
                  <div className="mt-0.5 text-slate-400">
                    <Files size={16} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-[11px] font-medium text-slate-500">
                      Document type
                    </p>
                    <p className="mt-1 break-words text-sm font-medium text-slate-800">
                      {selectedDocument.document_type?.replace(/_/g, " ") ||
                        "Not available"}
                    </p>
                  </div>
                </div>
                <div className="flex min-w-0 items-start gap-2 rounded-xl border border-slate-200 p-3">
                  <div className="mt-0.5 text-slate-400">
                    <CalendarDays size={16} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-[11px] font-medium text-slate-500">
                      Uploaded on
                    </p>
                    <p className="mt-1 break-words text-sm font-medium text-slate-800">
                      {selectedDocument.created_at
                        ? formatDate(selectedDocument.created_at)
                        : "Not available"}
                    </p>
                  </div>
                </div>
                <div className="flex min-w-0 items-start gap-2 rounded-xl border border-slate-200 p-3">
                  <div className="mt-0.5 text-slate-400">
                    <ShieldCheck size={16} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-[11px] font-medium text-slate-500">
                      Source
                    </p>
                    <p className="mt-1 break-words text-sm font-medium text-slate-800">
                      {(
                        selectedDocument.file_type ??
                        selectedDocument.mime_type ??
                        "File"
                      )
                        .toString()
                        .replace("application/", "")
                        .replace("image/", "")
                        .toUpperCase()}
                    </p>
                  </div>
                </div>
              </div>

              {familyMismatch && (
                <div
                  role="alert"
                  className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-sm text-amber-900"
                >
                  <AlertCircle
                    size={18}
                    className="mt-0.5 shrink-0"
                    aria-hidden="true"
                  />
                  <div className="min-w-0">
                    <p className="font-semibold">
                      This document appears to belong to another family
                    </p>
                    <p className="mt-1 break-words text-xs leading-relaxed">
                      The document mentions{" "}
                      <strong>{extractedFamilyName}</strong>, but the selected
                      family is <strong>{currentFamilyName}</strong>. Close this
                      document and switch to the correct family before
                      confirming it.
                    </p>
                  </div>
                </div>
              )}

              <section className="space-y-3">
                <div>
                  <h3 className="text-sm font-semibold text-slate-950">
                    Review extracted details
                  </h3>
                  <p className="mt-1 text-xs leading-relaxed text-slate-500">
                    Check the information below and correct anything that looks
                    wrong before saving.
                  </p>
                </div>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <label className="block min-w-0 sm:col-span-2">
                    <span className="mb-1.5 block text-xs font-medium text-slate-600">
                      Title <span className="text-rose-600">*</span>
                    </span>
                    <input
                      value={draft.title}
                      onChange={(event) =>
                        updateDraft("title", event.target.value)
                      }
                      maxLength={200}
                      className="w-full min-w-0 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
                      placeholder="e.g. Electricity bill"
                    />
                  </label>

                  <label className="block min-w-0">
                    <span className="mb-1.5 block text-xs font-medium text-slate-600">
                      Type <span className="text-rose-600">*</span>
                    </span>
                    <div className="relative">
                      <select
                        value={draft.commitment_type}
                        onChange={(event) =>
                          updateDraft("commitment_type", event.target.value)
                        }
                        className="w-full min-w-0 appearance-none rounded-xl border border-slate-200 bg-white px-3 py-2.5 pr-9 text-sm text-slate-900 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
                      >
                        {COMMITMENT_TYPES.map((item) => (
                          <option key={item.value} value={item.value}>
                            {item.label}
                          </option>
                        ))}
                      </select>
                      <ChevronDown
                        size={16}
                        className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                      />
                    </div>
                  </label>

                  <label className="block min-w-0">
                    <span className="mb-1.5 block text-xs font-medium text-slate-600">
                      Category
                    </span>
                    <input
                      value={draft.category}
                      onChange={(event) =>
                        updateDraft("category", event.target.value)
                      }
                      maxLength={50}
                      className="w-full min-w-0 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
                      placeholder="e.g. Utilities, School fees"
                    />
                  </label>

                  <label className="block min-w-0">
                    <span className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-slate-600">
                      <Wallet size={13} />
                      Amount (₹)
                    </span>
                    <input
                      type="number"
                      inputMode="decimal"
                      min="0.01"
                      step="0.01"
                      value={draft.amount}
                      onChange={(event) =>
                        updateDraft("amount", event.target.value)
                      }
                      className="w-full min-w-0 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
                      placeholder="Leave blank if not applicable"
                    />
                  </label>

                  <label className="block min-w-0">
                    <span className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-slate-600">
                      <UserRound size={13} />
                      Assign to family member
                    </span>
                    <div className="relative">
                      <select
                        value={draft.member_id}
                        onChange={(event) => updateMember(event.target.value)}
                        className="w-full min-w-0 appearance-none rounded-xl border border-slate-200 bg-white px-3 py-2.5 pr-9 text-sm text-slate-900 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
                      >
                        <option value="">No member assigned</option>
                        {members
                          .filter((member) => member.is_active)
                          .map((member) => (
                            <option key={member.id} value={member.id}>
                              {member.name}
                            </option>
                          ))}
                      </select>
                      <ChevronDown
                        size={16}
                        className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                      />
                    </div>
                    {draft.member_name &&
                      !members.some(
                        (member) =>
                          member.name.trim().toLowerCase() ===
                          draft.member_name.toLowerCase(),
                      ) && (
                        <span className="mt-1.5 block text-xs leading-relaxed text-amber-700">
                          The document names “{draft.member_name}”, which does
                          not match a member in the selected family. Choose a
                          member above or leave it unassigned.
                        </span>
                      )}
                  </label>

                  <label className="block min-w-0">
                    <span className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-slate-600">
                      <CalendarDays size={13} />
                      Event / start date
                    </span>
                    <input
                      type="date"
                      value={draft.start_date}
                      onChange={(event) =>
                        updateDraft("start_date", event.target.value)
                      }
                      className="w-full min-w-0 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
                    />
                  </label>

                  <label className="block min-w-0">
                    <span className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-slate-600">
                      <Clock3 size={13} />
                      Due date
                    </span>
                    <input
                      type="date"
                      value={draft.due_date}
                      onChange={(event) =>
                        updateDraft("due_date", event.target.value)
                      }
                      className="w-full min-w-0 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
                    />
                  </label>

                  <label className="block min-w-0 sm:col-span-2">
                    <span className="mb-1.5 block text-xs font-medium text-slate-600">
                      Notes / description
                    </span>
                    <textarea
                      rows={3}
                      maxLength={2000}
                      value={draft.description}
                      onChange={(event) =>
                        updateDraft("description", event.target.value)
                      }
                      className="w-full min-w-0 resize-y rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm leading-relaxed text-slate-900 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
                      placeholder="Additional context from the document"
                    />
                  </label>
                </div>
              </section>

              {additionalDetails.length > 0 && (
                <section className="overflow-hidden rounded-2xl border border-slate-200">
                  <button
                    type="button"
                    aria-expanded={showMoreDetails}
                    onClick={() => setShowMoreDetails((value) => !value)}
                    className="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left transition hover:bg-slate-50"
                  >
                    <span>
                      <span className="block text-sm font-semibold text-slate-900">
                        Other details found in the document
                      </span>
                      <span className="mt-0.5 block text-xs text-slate-500">
                        {additionalDetails.length} additional{" "}
                        {additionalDetails.length === 1 ? "field" : "fields"}
                      </span>
                    </span>
                    <ChevronDown
                      size={18}
                      className={`shrink-0 text-slate-500 transition-transform ${showMoreDetails ? "rotate-180" : ""}`}
                    />
                  </button>
                  {showMoreDetails && (
                    <div className="grid grid-cols-1 gap-0 border-t border-slate-100 sm:grid-cols-2">
                      {additionalDetails.map((item, index) => (
                        <div
                          key={`${item.label}-${index}`}
                          className="min-w-0 border-b border-slate-100 px-4 py-3 last:border-b-0 sm:even:border-l sm:even:border-l-slate-100"
                        >
                          <p className="text-[11px] font-medium text-slate-500">
                            {item.label}
                          </p>
                          <p className="mt-1 break-words text-sm leading-relaxed text-slate-800">
                            {item.value}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}

              {confirmError && (
                <div
                  role="alert"
                  className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700"
                >
                  <AlertCircle size={17} className="mt-0.5 shrink-0" />
                  <span className="break-words">{confirmError}</span>
                </div>
              )}
            </div>

            <footer className="shrink-0 border-t border-slate-100 bg-white px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:px-6 sm:py-4">
              {selectedDocument.processing_status === "NEEDS_CONFIRMATION" ? (
                <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end sm:gap-3">
                  <button
                    type="button"
                    onClick={closeDocument}
                    disabled={confirming}
                    className="inline-flex w-full items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50 sm:w-auto sm:py-2.5"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleConfirmSelectedDocument}
                    disabled={confirming || Boolean(familyMismatch)}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto sm:py-2.5"
                  >
                    {confirming ? (
                      <RefreshCw size={16} className="animate-spin" />
                    ) : (
                      <CheckCircle2 size={16} />
                    )}{" "}
                    {confirming ? "Saving…" : "Confirm and create commitment"}
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={closeDocument}
                  disabled={confirming}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50 sm:ml-auto sm:w-auto sm:py-2.5"
                >
                  <CheckCircle2 size={16} />
                  Done
                </button>
              )}
            </footer>
          </section>
        </div>
      )}
    </main>
  );
}
