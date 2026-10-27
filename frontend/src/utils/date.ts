export function parseLocalDate(value?: string | null): Date | null {
  if (!value) return null;

  // Parse date-only values in local time to avoid timezone shifts.
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);

  const date = match
    ? new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
    : new Date(value);

  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDate(value?: string | null): string {
  const date = parseLocalDate(value);
  if (!date) return "—";

  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = String(date.getFullYear()).slice(-2);

  return `${day}-${month}-${year}`;
}