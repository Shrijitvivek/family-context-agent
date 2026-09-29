/**
 * DocumentsPage
 *
 * Displays the family's uploaded documents and their processing status.
 *
 * Responsibilities:
 * - Fetch documents from the frontend API service.
 * - Display documents using the reusable DocumentCard component.
 * - Show loading, empty and error states.
 * - Provide a responsive document layout.
 */

import { useEffect, useState } from "react";
import PageHeader from "../components/ui/PageHeader";
import DocumentCard from "../components/documents/DocumentCard";
import {
  getDocuments,
  type DocumentResponse,
} from "../services/api/documents";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await getDocuments();
        setDocuments(data);
      } catch {
        setError("Unable to load documents. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    loadDocuments();
  }, []);

  return (
    <div>
      <PageHeader
        title="Documents"
        description="View and manage your family's important documents."
      />

      {loading && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
          Loading documents...
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {!loading && !error && documents.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
          <h2 className="text-lg font-semibold text-slate-900">
            No documents yet
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Uploaded family documents will appear here.
          </p>
        </div>
      )}

      {!loading && !error && documents.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {documents.map((document) => (
            <DocumentCard
              key={document.document_id}
              filename={document.filename}
              status={document.status}
            />
          ))}
        </div>
      )}
    </div>
  );
}