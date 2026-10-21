/**
 * DocumentsPage
 *
 * Displays the family's uploaded documents and their processing status.
 * Updated to match the refined minimalist design system.
 */

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  FileText,
  Upload,
  RefreshCw,
  Files,
  ShieldCheck,
  User,
} from "lucide-react";

import DocumentCard from "../components/documents/DocumentCard";

import {
  getDocuments,
  type DocumentResponse,
  uploadDocument,
  confirmDocument,
} from "../services/api/documents";

import { useFamily } from "../context/FamilyContext";

type IconName =
  | "calendar"
  | "check"
  | "wallet"
  | "file"
  | "flag"
  | "cart"
  | "medical"
  | "fuel"
  | "food"
  | "activity"
  | "clock"
  | "refresh"
  | "chevron"
  | "alert"
  | "sparkles"
  | "user"
  | "plus"
  | "upload"
  | "chat"
  | "arrow-right"
  | "receipt";

function Icon({
  name,
  size = 20,
  className = "",
}: {
  name: IconName;
  size?: number;
  className?: string;
}) {
  const shared = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className,
    "aria-hidden": true as const,
  };

  const drawings: Record<IconName, ReactNode> = {
    calendar: (
      <>
        <rect x="3.5" y="5" width="17" height="15.5" rx="2.5" />
        <path d="M7.5 3v4M16.5 3v4M3.5 10h17" />
      </>
    ),
    check: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="m8 12 2.5 2.5L16 9" />
      </>
    ),
    wallet: (
      <>
        <rect x="3" y="5" width="18" height="15" rx="2.5" />
        <path d="M3 9h18M16 14h2" />
      </>
    ),
    file: (
      <>
        <path d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
        <path d="M14 3v6h5M9 13h6M9 17h6" />
      </>
    ),
    flag: (
      <>
        <path d="M5 21V4" />
        <path d="M5 5c5-4 8 4 14 0v10c-6 4-9-4-14 0" />
      </>
    ),
    cart: (
      <>
        <path d="M3 4h2l2.2 11h10.9L21 8H6" />
        <circle cx="9" cy="19" r="1.2" />
        <circle cx="17" cy="19" r="1.2" />
      </>
    ),
    medical: (
      <>
        <rect x="3" y="4" width="18" height="16" rx="3" />
        <path d="M12 8v8M8 12h8" />
      </>
    ),
    fuel: (
      <>
        <path d="M5 21V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16M4 21h13M7 7h7" />
        <path d="M16 9h2l2 3v6a2 2 0 0 1-4 0v-3" />
      </>
    ),
    food: (
      <>
        <path d="M4 3v7a3 3 0 0 0 6 0V3M7 3v18M17 3v18M17 3c-4 4-4 9 0 10" />
      </>
    ),
    activity: <path d="M3 12h4l3-8 4 16 3-8h4" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    refresh: (
      <>
        <path d="M20 7v5h-5M4 17v-5h5" />
        <path d="M5.5 9a7 7 0 0 1 11.7-2L20 12M4 12l2.8 5a7 7 0 0 0 11.7-2" />
      </>
    ),
    chevron: <path d="m9 18 6-6-6-6" />,
    alert: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v5M12 16.5h.01" />
      </>
    ),
    sparkles: (
      <>
        <path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-2-5.8L4 11l6-2.2L12 3Z" />
        <path d="m19 14 1.1 2.2L22 17l-1.9.8L19 20l-.9-2.2L16 17l2.1-.8L19 14Z" />
      </>
    ),
    user: (
      <>
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    upload: (
      <>
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </>
    ),
    chat: (
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    ),
    "arrow-right": <path d="M5 12h14M12 5l7 7-7 7" />,
    receipt: (
      <>
        <path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2L18 3l-2-1-2 1-2-1-2 1-2-1-2 1-2-1Z" />
        <path d="M8 8h8M8 12h8M8 16h5" />
      </>
    ),
  };

  return <svg {...shared}>{drawings[name]}</svg>;
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

function IconTile({
  icon,
  tone = "violet",
  size = "md",
}: {
  icon: IconName;
  tone?: "violet" | "blue" | "green" | "amber" | "rose" | "slate";
  size?: "sm" | "md" | "lg";
}) {
  const tones = {
    violet: "bg-violet-50 text-violet-700 ring-violet-100/70",
    blue: "bg-blue-50 text-blue-700 ring-blue-100/70",
    green: "bg-emerald-50 text-emerald-700 ring-emerald-100/70",
    amber: "bg-amber-50 text-amber-700 ring-amber-100/70",
    rose: "bg-rose-50 text-rose-700 ring-rose-100/70",
    slate: "bg-slate-100 text-slate-700 ring-slate-200/60",
  };

  const dimensions = {
    sm: "size-9 rounded-xl",
    md: "size-11 rounded-xl",
    lg: "size-12 rounded-[14px]",
  };

  const iconSize = size === "sm" ? 17 : size === "lg" ? 22 : 20;

  return (
    <div
      className={`inline-flex shrink-0 items-center justify-center ring-1 ring-inset ${tones[tone]} ${dimensions[size]}`}
    >
      <Icon name={icon} size={iconSize} />
    </div>
  );
}

export default function DocumentsPage() {
  const { selectedFamilyId, selectedMemberId } = useFamily();

  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [selectedDocument, setSelectedDocument] =
    useState<DocumentResponse | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
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

        if (!cancelled) {
          setDocuments(data);
        }
      } catch {
        if (!cancelled) {
          setError("Unable to load documents. Please try again.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadDocuments();

    return () => {
      cancelled = true;
    };
  }, [selectedFamilyId, selectedMemberId, retryCount]);

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (!file || !selectedFamilyId) {
      return;
    }

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

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleConfirmSelectedDocument = async () => {
    if (!selectedDocument || !selectedFamilyId) return;

    const data = selectedDocument.extracted_data ?? {};
    const title = data.title;
    const commitmentType = data.commitment_type;

    if (
      typeof title !== "string" ||
      !title.trim() ||
      typeof commitmentType !== "string" ||
      !commitmentType.trim()
    ) {
      setConfirmError("The document is missing a title or commitment type.");
      return;
    }

    setConfirming(true);
    setConfirmError("");

    try {
      const rawAmount = data.amount;
      const amount =
        typeof rawAmount === "number"
          ? rawAmount
          : typeof rawAmount === "string" && rawAmount.trim()
            ? Number(rawAmount)
            : undefined;

      await confirmDocument(selectedDocument.id, {
        family_id: selectedFamilyId,
        member_id: selectedMemberId || undefined,
        commitment_type: commitmentType,
        title,
        category: typeof data.category === "string" ? data.category : undefined,
        description:
          typeof data.description === "string" ? data.description : undefined,
        amount:
          amount !== undefined && Number.isFinite(amount) ? amount : undefined,
        start_date:
          typeof data.start_date === "string" ? data.start_date : undefined,
        due_date: typeof data.due_date === "string" ? data.due_date : undefined,
        priority: "MEDIUM",
      });

      const updatedDocuments = await getDocuments(
        selectedFamilyId,
        selectedMemberId,
      );

      setDocuments(updatedDocuments);
      setSelectedDocument(null);
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

  return (
    <main className="mx-auto w-full max-w-[1600px] space-y-5 pb-8 sm:space-y-6 font-sans">
      {/* Page header */}
      <Surface className="p-6 sm:p-8 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
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
            View and manage your family's important documents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label
            htmlFor="document-upload"
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold shadow-sm transition cursor-pointer ${
              uploading || !selectedFamilyId
                ? "cursor-not-allowed bg-slate-100 text-slate-400 border border-slate-200"
                : "bg-slate-900 text-white hover:bg-slate-800"
            }`}
          >
            {uploading ? (
              <>
                <RefreshCw
                  size={14}
                  className="animate-spin"
                  aria-hidden="true"
                />
                Uploading...
              </>
            ) : (
              <>
                <Upload size={14} aria-hidden="true" />
                Upload document
              </>
            )}

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
        </div>
      </Surface>

      {/* Upload info banner */}
      <Surface className="p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500 bg-slate-50/50">
        <div className="flex items-center gap-2">
          <FileText size={15} className="text-slate-400" aria-hidden="true" />
          <span>Supported formats: PDF, JPG, JPEG, PNG</span>
        </div>
        <div className="flex items-center gap-2">
          <ShieldCheck
            size={15}
            className="text-emerald-600"
            aria-hidden="true"
          />
          <span>Securely stored & processed</span>
        </div>
      </Surface>

      {/* Error state */}
      {error && (
        <div
          role="alert"
          className="flex flex-col gap-3 rounded-2xl border border-rose-200 bg-rose-50/70 p-5 sm:flex-row sm:items-center sm:justify-between shadow-sm"
        >
          <div>
            <p className="text-sm font-semibold text-rose-800">
              Something went wrong
            </p>
            <p className="mt-1 text-sm text-rose-700">{error}</p>
          </div>

          <button
            type="button"
            onClick={() => setRetryCount((count) => count + 1)}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-xs font-semibold text-rose-700 shadow-sm border border-rose-200 hover:bg-rose-50 transition disabled:opacity-60"
          >
            <RefreshCw size={14} aria-hidden="true" />
            Try again
          </button>
        </div>
      )}

      {/* Documents list section */}
      <Surface className="p-5 sm:p-6">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold tracking-tight text-slate-950">
              Your documents
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Your family's uploaded files and processing status.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {selectedMemberId && (
              <span className="inline-flex items-center gap-1.5 rounded-xl border border-violet-100 bg-violet-50/70 px-3 py-1 text-xs font-medium text-violet-700">
                <User size={13} aria-hidden="true" />
                Member filtered
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
              <Files size={13} aria-hidden="true" />
              {documents.length}{" "}
              {documents.length === 1 ? "document" : "documents"}
            </span>
          </div>
        </div>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 py-4">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="rounded-2xl border border-slate-200 bg-slate-50/50 p-5 space-y-3"
              >
                <div className="h-10 w-10 animate-pulse rounded-xl bg-slate-200" />
                <div className="h-4 w-3/4 animate-pulse rounded bg-slate-200" />
                <div className="h-3 w-1/2 animate-pulse rounded bg-slate-200" />
              </div>
            ))}
          </div>
        ) : !selectedFamilyId ? (
          <div className="rounded-2xl border border-dashed border-slate-200 px-5 py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
              <Files size={22} aria-hidden="true" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900">
              Select a family
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Choose a family to view and manage its documents.
            </p>
          </div>
        ) : documents.length === 0 && !error ? (
          <div className="rounded-2xl border border-dashed border-slate-200 px-5 py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
              <FileText size={22} aria-hidden="true" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900">
              No documents yet
            </h3>
            <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
              Upload your first family document using the button above. Your
              uploaded documents will appear here.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {documents.map((document) => (
              <button
                key={document.id}
                type="button"
                onClick={() => setSelectedDocument(document)}
                className="w-full cursor-pointer rounded-2xl text-left transition hover:-translate-y-0.5 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-violet-500"
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
      {selectedDocument && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4"
          onClick={() => setSelectedDocument(null)}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-details-title"
            className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <h2
                  id="document-details-title"
                  className="text-lg font-semibold text-slate-900"
                >
                  Document details
                </h2>
                <p className="mt-1 break-words text-sm text-slate-500">
                  {selectedDocument.file_name}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedDocument(null)}
                className="rounded-lg px-3 py-1 text-sm text-slate-500 hover:bg-slate-100"
              >
                Close
              </button>
            </div>

            <div className="mt-5 space-y-3 text-sm">
              <div className="flex justify-between gap-4">
                <span className="text-slate-500">Status</span>
                <span className="break-words text-right font-medium text-slate-900">
                  {(selectedDocument.processing_status ?? "UNKNOWN").replace(
                    /_/g,
                    " ",
                  )}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-slate-500">Document type</span>
                <span className="break-words text-right text-slate-900">
                  {selectedDocument.document_type || "Not available"}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-slate-500">Uploaded on</span>
                <span className="text-right text-slate-900">
                  {selectedDocument.created_at
                    ? new Date(selectedDocument.created_at).toLocaleDateString()
                    : "Not available"}
                </span>
              </div>
            </div>

            <div className="mt-5 border-t border-slate-100 pt-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-900">
                Extracted details
              </h3>

              {selectedDocument.extracted_data &&
              Object.keys(selectedDocument.extracted_data).length > 0 ? (
                <div className="max-h-64 space-y-3 overflow-y-auto">
                  {Object.entries(selectedDocument.extracted_data).map(
                    ([key, value]) => (
                      <div key={key}>
                        <p className="text-xs font-medium text-slate-500">
                          {key
                            .replace(/_/g, " ")
                            .replace(/\b\w/g, (letter) => letter.toUpperCase())}
                        </p>
                        <p className="mt-1 break-words text-sm text-slate-800">
                          {value === null || value === undefined
                            ? "Not available"
                            : typeof value === "object"
                              ? JSON.stringify(value, null, 2)
                              : String(value)}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              ) : (
                <p className="text-sm text-slate-500">
                  No extracted details available for this document.
                </p>
              )}
            </div>

            <button
              type="button"
              onClick={() => setSelectedDocument(null)}
              className="mt-5 w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
            >
              Done
            </button>
            {selectedDocument.processing_status === "NEEDS_CONFIRMATION" && (
              <>
                {confirmError && (
                  <p role="alert" className="mt-3 text-sm text-red-600">
                    {confirmError}
                  </p>
                )}

                <button
                  type="button"
                  onClick={handleConfirmSelectedDocument}
                  disabled={confirming}
                  className="mt-5 w-full rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60"
                >
                  {confirming
                    ? "Confirming..."
                    : "Confirm and create commitment"}
                </button>
              </>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
