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

interface DocumentCardProps {
  filename: string;
  status: string;
}

export default function DocumentCard({
  filename,
  status,
}: DocumentCardProps) {
  return (
    <Card className="flex items-center justify-between gap-4">
      <div className="min-w-0">
        <h2 className="truncate font-medium text-slate-900">
          {filename}
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Family document
        </p>
      </div>

      <StatusBadge status={status} />
    </Card>
  );
}