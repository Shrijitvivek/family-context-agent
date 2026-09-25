/**
 * StatusBadge
 *
 * Provides a reusable status indicator for the Family Context application.
 *
 * Responsibilities:
 * - Display common item statuses consistently.
 * - Use different visual styles for different statuses.
 * - Reuse the same status design across Timeline, Expenses and Documents.
 */

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const normalizedStatus = status.toLowerCase();

  const styles =
    normalizedStatus === "completed"
      ? "bg-green-100 text-green-700"
      : normalizedStatus === "pending"
        ? "bg-yellow-100 text-yellow-700"
        : normalizedStatus === "overdue"
          ? "bg-red-100 text-red-700"
          : "bg-slate-100 text-slate-600";

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${styles}`}
    >
      {status}
    </span>
  );
}