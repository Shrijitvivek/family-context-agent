/**
 * DocumentsPage
 *
 * Displays the family's uploaded documents and their processing status.
 */

import { useEffect, useRef, useState } from "react";

import {
  FileText,
  Upload,
  RefreshCw,
  Files,
  ShieldCheck,
  User,
} from "lucide-react";

import PageHeader from "../components/ui/PageHeader";
import DocumentCard from "../components/documents/DocumentCard";

import {
  getDocuments,
  type DocumentResponse,
  uploadDocument,
} from "../services/api/documents";

import { useFamily } from "../context/FamilyContext";

export default function DocumentsPage() {
  const { selectedFamilyId, selectedMemberId } = useFamily();

  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
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

  const handleUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
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

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-7 sm:px-6 sm:py-9 lg:px-8">
      {/* Page header */}
      <PageHeader
        title="Documents"
        description="View and manage your family's important documents."
      />

      {/* Upload section */}
      <section
        aria-label="Upload documents"
        className="mt-6 overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-sm"
      >
        <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-50/70 text-violet-600 ring-1 ring-inset ring-violet-100/70">
              <Upload size={20} aria-hidden="true" />
            </div>

            <div>
              <h2 className="text-sm font-semibold text-slate-900">
                Upload a document
              </h2>

              <p className="mt-1 text-sm leading-5 text-slate-500">
                Add important family documents to keep them organized in one place.
              </p>
            </div>
          </div>

          <label
            htmlFor="document-upload"
            className={`inline-flex min-h-10 shrink-0 cursor-pointer items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-colors focus-within:ring-2 focus-within:ring-violet-400 focus-within:ring-offset-2 ${
              uploading || !selectedFamilyId
                ? "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400"
                : "border-violet-200 bg-violet-50 text-violet-800 hover:bg-violet-100"
            }`}
          >
            {uploading ? (
              <>
                <RefreshCw
                  size={16}
                  className="animate-spin"
                  aria-hidden="true"
                />
                Uploading...
              </>
            ) : (
              <>
                <Upload size={16} aria-hidden="true" />
                Choose file
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

        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-slate-100 bg-slate-50/60 px-5 py-3 sm:px-6">
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
            <FileText size={14} aria-hidden="true" />
            PDF, JPG, JPEG, PNG
          </span>

          <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
            <ShieldCheck size={14} aria-hidden="true" />
            Supported document formats
          </span>
        </div>
      </section>

      {/* Error state */}
      {error && (
        <div
          role="alert"
          className="mt-5 flex flex-col gap-3 rounded-xl border border-rose-200 bg-rose-50/70 p-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <p className="text-sm font-semibold text-rose-800">
              Something went wrong
            </p>

            <p className="mt-1 break-words text-sm leading-5 text-rose-700">
              {error}
            </p>
          </div>

          <button
            type="button"
            onClick={() => setRetryCount((count) => count + 1)}
            disabled={loading}
            className="inline-flex w-fit shrink-0 items-center justify-center gap-2 rounded-lg border border-rose-200 bg-white px-3.5 py-2 text-sm font-semibold text-rose-700 transition-colors hover:bg-rose-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw size={14} aria-hidden="true" />
            Try again
          </button>
        </div>
      )}

      {/* Documents list */}
      <section aria-label="Family documents" className="mt-8">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold tracking-tight text-slate-900">
              Your documents
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Your family's uploaded files and processing status.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {selectedMemberId && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-violet-100 bg-violet-50/70 px-3 py-1.5 text-xs font-medium text-violet-700">
                <User size={13} aria-hidden="true" />
                Member filtered
              </span>
            )}

            <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600">
              <Files size={13} aria-hidden="true" />
              {documents.length}{" "}
              {documents.length === 1 ? "document" : "documents"}
            </span>
          </div>
        </div>

        {/* Loading state */}
        {loading ? (
          <div
            aria-label="Loading documents"
            aria-busy="true"
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="rounded-2xl border border-slate-200 bg-white p-5"
              >
                <div className="flex items-start gap-3">
                  <div className="h-11 w-11 shrink-0 animate-pulse rounded-xl bg-slate-100" />

                  <div className="min-w-0 flex-1 space-y-2 pt-1">
                    <div className="h-4 w-32 max-w-full animate-pulse rounded bg-slate-100" />
                    <div className="h-3 w-24 animate-pulse rounded bg-slate-100" />
                  </div>
                </div>

                <div className="mt-6 h-8 w-24 animate-pulse rounded-lg bg-slate-100" />
              </div>
            ))}
          </div>
        ) : !selectedFamilyId ? (
          /* No family selected */
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
              <Files size={22} aria-hidden="true" />
            </div>

            <h3 className="mt-4 text-sm font-semibold text-slate-900">
              Select a family
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              Choose a family to view and manage its documents.
            </p>
          </div>
        ) : documents.length === 0 && !error ? (
          /* Empty state */
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50/70 text-violet-600 ring-1 ring-inset ring-violet-100/70">
              <FileText size={22} aria-hidden="true" />
            </div>

            <h3 className="mt-4 text-sm font-semibold text-slate-900">
              No documents yet
            </h3>

            <p className="mx-auto mt-1 max-w-sm text-sm leading-6 text-slate-500">
              Upload your first family document using the button above. Your uploaded documents will appear here.
            </p>
          </div>
        ) : (
          /* Documents grid */
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {documents.map((document) => (
              <DocumentCard
                key={document.id}
                filename={document.file_name}
                status={document.processing_status ?? "UNKNOWN"}
              />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}