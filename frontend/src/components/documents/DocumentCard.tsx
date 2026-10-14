/**
 * DocumentCard
 *
 * Displays a single family document in the Documents page.
 *
 * Responsibilities:
 * - Display the document filename.
 * - Display the document processing status.
 * - Provide a consistent visual container for documents.
 */

import Card from "../ui/Card";
import StatusBadge from "../ui/StatusBadge";
import { useState } from "react";
import ExtractionConfirmation from "./ExtractionConfirmation";
import type { ConfirmedCommitment, DocumentResponse } from "../../services/api/documents";

interface DocumentCardProps {
  document: DocumentResponse;
  familyId: string;
  onConfirmed: (documentId: string, commitment: ConfirmedCommitment) => void;
}

export default function DocumentCard({
  document,
  familyId,
  onConfirmed,
}: DocumentCardProps) {
  const [confirmedCommitment, setConfirmedCommitment] = useState<ConfirmedCommitment | null>(null);
  const status = confirmedCommitment ? "CONFIRMED" : document.processing_status ?? "UNKNOWN";

  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <h2 className="truncate font-medium text-slate-900">{document.file_name}</h2>

          <p className="mt-1 text-sm text-slate-500">Family document</p>
        </div>
        <StatusBadge status={status} />
      </div>

      {status === "NEEDS_CONFIRMATION" && (
        <ExtractionConfirmation
          document={document}
          familyId={familyId}
          onConfirmed={(commitment) => {
            setConfirmedCommitment(commitment);
            onConfirmed(document.id, commitment);
          }}
        />
      )}
      {confirmedCommitment && (
        <p role="status" className="mt-3 text-sm text-emerald-700">
          Confirmed: {confirmedCommitment.title}
        </p>
      )}
    </Card>
  );
}
