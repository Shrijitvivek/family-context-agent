export const DEFAULT_FAMILY_TIMEZONE = "Asia/Kolkata";

export interface FamilyCalendarDate {
  year: number;
  month: number;
  day: number;
  headerLabel: string;
  monthYearLabel: string;
  firstWeekday: number;
  daysInMonth: number;
}

export function getFamilyCalendarDate(
  timezone: string | null | undefined,
  now: Date = new Date(),
): FamilyCalendarDate {
  const requestedTimezone = timezone || DEFAULT_FAMILY_TIMEZONE;
  let effectiveTimezone = requestedTimezone;
  let parts: Intl.DateTimeFormatPart[];

  try {
    parts = new Intl.DateTimeFormat("en-IN", {
      timeZone: effectiveTimezone,
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }).formatToParts(now);
  } catch {
    // The backend Family model and application configuration both default to this zone.
    effectiveTimezone = DEFAULT_FAMILY_TIMEZONE;
    parts = new Intl.DateTimeFormat("en-IN", {
      timeZone: effectiveTimezone,
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }).formatToParts(now);
  }

  const value = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value ?? "";
  const year = Number(value("year"));
  const monthName = value("month");
  const month = Number(new Intl.DateTimeFormat("en-US", {
    timeZone: effectiveTimezone,
    month: "numeric",
  }).format(now));
  const day = Number(value("day"));

  return {
    year,
    month,
    day,
    headerLabel: `${value("weekday")}, ${day} ${monthName} ${year}`.toUpperCase(),
    monthYearLabel: `${monthName} ${year}`,
    firstWeekday: new Date(Date.UTC(year, month - 1, 1)).getUTCDay(),
    daysInMonth: new Date(Date.UTC(year, month, 0)).getUTCDate(),
  };
}
