/**
 * DocumentsPage
 *
 * Displays the family's uploaded documents and their processing status.
 */

import { useEffect, useState } from "react";
import PageHeader from "../components/ui/PageHeader";
import DocumentCard from "../components/documents/DocumentCard";
import {
  getDocuments,
  type DocumentResponse,
  uploadDocument,
} from "../services/api/documents";
import { useFamily } from "../context/FamilyContext";

export default function DocumentsPage() {
  const { selectedFamilyId } = useFamily();

  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    const loadDocuments = async () => {
      if (!selectedFamilyId) {
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const data = await getDocuments(selectedFamilyId);
        setDocuments(data);
      } catch {
        setError("Unable to load documents. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    loadDocuments();
  }, [selectedFamilyId]);

  return (
    <div>
      <PageHeader
        title="Documents"
        description="View and manage your family's important documents."
      />

      <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5">
        <label
          htmlFor="document-upload"
          className="block text-sm font-medium text-slate-700"
        >
          Upload a document
        </label>

        <input
          id="document-upload"
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          disabled={uploading || !selectedFamilyId}
          className="mt-3 block w-full text-sm text-slate-600"
          onChange={async (event) => {
            const file = event.target.files?.[0];

            if (!file || !selectedFamilyId) {
              return;
            }

            try {
              setUploading(true);
              setError(null);

              await uploadDocument(selectedFamilyId, file);

              const data = await getDocuments(selectedFamilyId);
              setDocuments(data);

              event.target.value = "";
            } catch (err) {
              setError(
                err instanceof Error
                  ? err.message
                  : "Unable to upload document.",
              );
            } finally {
              setUploading(false);
            }
          }}
        />
      </div>

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
              key={document.id}
              filename={document.file_name}
              status={document.processing_status ?? "UNKNOWN"}
            />
          ))}
        </div>
      )}
    </div>
  );
}
