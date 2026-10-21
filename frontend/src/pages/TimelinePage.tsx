/**
 * TimelinePage.tsx
 *
 * Displays the family's commitments, timeline events, and priority items.
 * Updated to match the refined minimalist design system.
 */

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  CalendarDays,
  UserRound,
  Clock3,
  ListFilter,
  RefreshCw,
  AlertCircle,
  CalendarCheck,
  User,
} from "lucide-react";

import { useFamily } from "../context/FamilyContext";
import type { TimelineResponse } from "../types/api";
import type { Commitment, CommitmentStatus } from "../types/domain";
import { getTimeline } from "../services/api/timeline";

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
  | "arrow-right";

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

const filters: Array<"all" | CommitmentStatus> = [
  "all",
  "pending",
  "scheduled",
  "in_progress",
  "completed",
  "overdue",
  "cancelled",
];

const statusStyles: Record<CommitmentStatus, string> = {
  pending: "bg-amber-100 text-amber-700",
  scheduled: "bg-slate-100 text-slate-700",
  in_progress: "bg-blue-100 text-blue-700",
  completed: "bg-emerald-100 text-emerald-700",
  overdue: "bg-rose-100 text-rose-700",
  cancelled: "bg-slate-100 text-slate-700",
};

const priorityStyles: Record<Exclude<Commitment["priority"], null>, string> = {
  low: "bg-slate-100 text-slate-700",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-amber-100 text-amber-700",
  critical: "bg-rose-100 text-rose-700",
};

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatStatus(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function EmptyState({
  filtered,
}: {
  filtered: boolean;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-5 py-14 text-center sm:py-20">
      <div className="flex size-12 items-center justify-center rounded-2xl bg-violet-50 text-violet-600">
        {filtered ? (
          <ListFilter size={22} aria-hidden="true" />
        ) : (
          <CalendarCheck size={22} aria-hidden="true" />
        )}
      </div>

      <h2 className="mt-4 text-sm font-semibold text-slate-900">
        {filtered ? "No matching commitments" : "Your timeline is clear"}
      </h2>

      <p className="mt-1 max-w-sm text-xs leading-relaxed text-slate-500">
        {filtered
          ? "Try selecting another status filter to see more commitments."
          : "Family commitments will appear here when they are added."}
      </p>
    </div>
  );
}

export default function TimelinePage() {
  const { selectedFamilyId, selectedMemberId, members } = useFamily();

  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<(typeof filters)[number]>("all");
  const [retryKey, setRetryKey] = useState(0);

  const selectedMember = members.find(
    (member) => member.id === selectedMemberId,
  );

  useEffect(() => {
    let cancelled = false;

    if (!selectedFamilyId) {
      setTimeline(null);
      setError(null);
      setLoading(false);
      return;
    }

    async function loadTimeline() {
      setLoading(true);
      setError(null);

      try {
        const data = await getTimeline(selectedFamilyId!);

        if (!cancelled) {
          setTimeline(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load the family timeline.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadTimeline();

    return () => {
      cancelled = true;
    };
  }, [selectedFamilyId, retryKey]);

  const timelineItems = timeline?.items ?? [];

  const memberItems = useMemo(
    () =>
      selectedMemberId
        ? timelineItems.filter(
            (item) => item.memberId === selectedMemberId || item.memberId == null,
          )
        : timelineItems,
    [timelineItems, selectedMemberId],
  );

  const visibleItems = useMemo(
    () =>
      filter === "all"
        ? memberItems
        : memberItems.filter((item) => item.status === filter),
    [filter, memberItems],
  );

  const counts = useMemo(
    () => ({
      all: memberItems.length,
      pending: memberItems.filter((item) => item.status === "pending").length,
      scheduled: memberItems.filter((item) => item.status === "scheduled").length,
      in_progress: memberItems.filter((item) => item.status === "in_progress").length,
      completed: memberItems.filter((item) => item.status === "completed").length,
      overdue: memberItems.filter((item) => item.status === "overdue").length,
      cancelled: memberItems.filter((item) => item.status === "cancelled").length,
    }),
    [memberItems],
  );

  return (
    <main className="mx-auto w-full max-w-[1600px] space-y-5 pb-8 sm:space-y-6 font-sans">
      {/* Page header */}
      <Surface className="p-6 sm:p-8 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-violet-100 bg-violet-50/70 px-3 py-1.5">
            <CalendarDays aria-hidden="true" size={14} className="text-violet-600" />
            <span className="text-xs font-semibold text-violet-700">
              Family commitments
            </span>
          </div>

          <h1 className="text-3xl font-bold tracking-[-0.055em] text-slate-950 sm:text-4xl">
            Timeline
          </h1>

          <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-600">
            {selectedMember
              ? `Important commitments for ${selectedMember.name}, including shared commitments.`
              : "Keep track of upcoming commitments, important dates, and everything that needs attention."}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setRetryKey((value) => value + 1)}
          disabled={loading || !selectedFamilyId}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white shadow hover:bg-slate-800 transition disabled:opacity-50"
        >
          <RefreshCw
            size={14}
            className={loading ? "animate-spin" : ""}
            aria-hidden="true"
          />
          Refresh timeline
        </button>
      </Surface>

      {/* Summary cards row */}
      <section
        aria-label="Timeline summary"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <Surface className="p-5 flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-500">
              All commitments
            </p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
              {loading ? "—" : counts.all}
            </p>
            <p className="mt-1 text-xs text-slate-400 font-medium truncate">
              {selectedMember ? `For ${selectedMember.name}` : "Total in timeline"}
            </p>
          </div>
          <IconTile icon="calendar" tone="violet" size="md" />
        </Surface>

        <Surface className="p-5 flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-500">Pending</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
              {loading ? "—" : counts.pending}
            </p>
            <p className="mt-1 text-xs text-amber-600 font-medium">
              Awaiting completion
            </p>
          </div>
          <IconTile icon="clock" tone="amber" size="md" />
        </Surface>

        <Surface className="p-5 flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-500">Completed</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
              {loading ? "—" : counts.completed}
            </p>
            <p className="mt-1 text-xs text-emerald-600 font-medium">
              Successfully done
            </p>
          </div>
          <IconTile icon="check" tone="green" size="md" />
        </Surface>

        <Surface className="p-5 flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-500">Overdue</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
              {loading ? "—" : counts.overdue}
            </p>
            <p className="mt-1 text-xs text-rose-600 font-medium">
              Needs attention
            </p>
          </div>
          <IconTile icon="alert" tone="rose" size="md" />
        </Surface>
      </section>

      {/* Timeline main container */}
      <Surface className="p-5 sm:p-6">
        {/* Filters bar */}
        <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-slate-950">
                All commitments
              </h2>
              {selectedMember && (
                <span className="inline-flex items-center gap-1 rounded-xl border border-violet-100 bg-violet-50/70 px-2.5 py-0.5 text-xs font-medium text-violet-700">
                  <User size={12} aria-hidden="true" />
                  {selectedMember.name}
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Review and filter your family's schedule.
            </p>
          </div>

          <div
            className="flex max-w-full gap-1.5 overflow-x-auto pb-1"
            role="group"
            aria-label="Filter commitments by status"
          >
            {filters.map((option) => {
              const selected = filter === option;
              const count =
                option === "all"
                  ? counts.all
                  : counts[option as keyof typeof counts];

              return (
                <button
                  key={option}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => setFilter(option)}
                  className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                    selected
                      ? "bg-slate-900 text-white shadow-xs"
                      : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {formatStatus(option)}
                  <span
                    className={`rounded-md px-1.5 py-0.5 text-[10px] tabular-nums ${
                      selected
                        ? "bg-slate-800 text-slate-200"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Error state */}
        {error && (
          <div
            role="alert"
            className="m-2 flex flex-col gap-3 rounded-2xl border border-rose-200 bg-rose-50/70 p-4 sm:flex-row sm:items-center sm:justify-between shadow-sm"
          >
            <div className="flex items-start gap-3">
              <AlertCircle
                size={18}
                className="mt-0.5 shrink-0 text-rose-700"
                aria-hidden="true"
              />
              <div>
                <p className="text-xs font-semibold text-rose-800">
                  Unable to load timeline
                </p>
                <p className="mt-0.5 text-xs text-rose-700">{error}</p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setRetryKey((value) => value + 1)}
              className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-white px-3 py-1.5 text-xs font-semibold text-rose-700 shadow-xs hover:bg-rose-50 transition"
            >
              Try again
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading ? (
          <div className="space-y-3 py-4" role="status">
            {[1, 2, 3].map((row) => (
              <div
                key={row}
                className="h-12 w-full animate-pulse rounded-xl bg-slate-100"
              />
            ))}
          </div>
        ) : !selectedFamilyId ? (
          <EmptyState filtered={false} />
        ) : visibleItems.length === 0 ? (
          <EmptyState filtered={filter !== "all" && memberItems.length > 0} />
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-200/80">
            {/* Desktop table heading */}
            <div className="hidden grid-cols-[minmax(0,1fr)_9rem_9rem] gap-4 border-b border-slate-200/80 bg-slate-50/70 px-5 py-3 text-xs font-semibold text-slate-500 md:grid">
              <span>Commitment</span>
              <span>Status</span>
              <span>Priority</span>
            </div>

            <div className="divide-y divide-slate-100">
              {visibleItems.map((item) => (
                <div
                  key={item.id}
                  className="grid gap-3 px-4 py-3.5 transition hover:bg-slate-50/70 sm:px-5 sm:py-3.5 md:grid-cols-[minmax(0,1fr)_9rem_9rem] md:items-center md:gap-4"
                >
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-900 truncate">
                      {item.title}
                    </p>
                    {item.description && (
                      <p className="text-[11px] text-slate-500 truncate mt-0.5">
                        {item.description}
                      </p>
                    )}

                    <div className="mt-1.5 flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
                      {item.familyMember && (
                        <span className="inline-flex items-center gap-1">
                          <UserRound size={12} aria-hidden="true" />
                          <span>{item.familyMember}</span>
                        </span>
                      )}

                      <span className="inline-flex items-center gap-1">
                        <Clock3 size={12} aria-hidden="true" />
                        <span>Due {formatDate(item.dueDate)}</span>
                      </span>
                    </div>
                  </div>

                  {/* Status */}
                  <div className="hidden md:block">
                    <span
                      className={`inline-flex rounded-md px-2.5 py-0.5 text-[10px] font-semibold ${statusStyles[item.status]}`}
                    >
                      {formatStatus(item.status)}
                    </span>
                  </div>

                  {/* Priority */}
                  <div className="hidden md:block">
                    {item.priority && (
                      <span
                        className={`inline-flex rounded-md px-2.5 py-0.5 text-[10px] font-semibold ${priorityStyles[item.priority]}`}
                      >
                        {formatStatus(item.priority)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        {!loading && !error && selectedFamilyId && visibleItems.length > 0 && (
          <div className="mt-4 flex flex-col gap-1.5 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <span>
              Showing{" "}
              <strong className="font-semibold text-slate-900">
                {visibleItems.length}
              </strong>{" "}
              of {memberItems.length} commitments
            </span>
            <span>Sorted according to your timeline data</span>
          </div>
        )}
      </Surface>
    </main>
  );
}
