import { useEffect, useMemo, useState } from "react";
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

const filters: Array<"all" | CommitmentStatus> = [
  "all",
  "pending",
  "completed",
  "overdue",
];

const statusStyles: Record<CommitmentStatus, string> = {
  pending: "bg-amber-50 text-amber-800 ring-amber-200",
  completed: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  overdue: "bg-rose-50 text-rose-800 ring-rose-200",
  cancelled: "bg-slate-100 text-slate-700 ring-slate-200",
};

const priorityStyles: Record<Commitment["priority"], string> = {
  low: "bg-slate-100 text-slate-700",
  medium: "bg-blue-50 text-blue-800",
  high: "bg-orange-50 text-orange-800",
  urgent: "bg-rose-50 text-rose-800",
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
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function SummaryCard({
  label,
  value,
  description,
  accent,
}: {
  label: string;
  value: number;
  description: string;
  accent: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.025)] sm:p-5">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className={`mt-3 text-3xl font-semibold tracking-tight ${accent}`}>
        {value}
      </p>
      <p className="mt-1.5 text-xs leading-5 text-slate-500">
        {description}
      </p>
    </div>
  );
}

function EmptyState({
  filtered,
}: {
  filtered: boolean;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-5 py-14 text-center sm:py-20">
      <div className="flex size-14 items-center justify-center rounded-2xl bg-violet-50 text-violet-600 ring-1 ring-inset ring-violet-100">
        {filtered ? (
          <ListFilter size={24} aria-hidden="true" />
        ) : (
          <CalendarCheck size={24} aria-hidden="true" />
        )}
      </div>

      <h2 className="mt-4 text-base font-semibold text-slate-900">
        {filtered
          ? "No matching commitments"
          : "Your timeline is clear"}
      </h2>

      <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
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

  // Filter items for selected member or shared items
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
      completed: memberItems.filter((item) => item.status === "completed").length,
      overdue: memberItems.filter((item) => item.status === "overdue").length,
    }),
    [memberItems],
  );

  return (
    <main className="mx-auto w-full max-w-[1600px] space-y-5 pb-8 sm:space-y-6">
      {/* Page heading */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-violet-600">
            <CalendarDays size={15} aria-hidden="true" />
            Family commitments
          </div>

          <h1 className="text-2xl font-bold tracking-[-0.04em] text-slate-950 sm:text-3xl">
            Timeline
          </h1>

          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500 sm:text-[15px]">
            {selectedMember
              ? `Important commitments for ${selectedMember.name}, including shared commitments.`
              : "Keep track of upcoming commitments, important dates, and everything that needs your family's attention."}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setRetryKey((value) => value + 1)}
          disabled={loading || !selectedFamilyId}
          className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
        >
          <RefreshCw
            size={15}
            className={loading ? "animate-spin" : ""}
            aria-hidden="true"
          />
          Refresh timeline
        </button>
      </header>

      {/* Summary cards */}
      <section
        aria-label="Timeline summary"
        className="grid grid-cols-2 gap-3 xl:grid-cols-4"
      >
        <SummaryCard
          label="All commitments"
          value={counts.all}
          description={selectedMember ? `Visible for ${selectedMember.name}` : "Total in your timeline"}
          accent="text-slate-950"
        />
        <SummaryCard
          label="Pending"
          value={counts.pending}
          description="Awaiting completion"
          accent="text-amber-700"
        />
        <SummaryCard
          label="Completed"
          value={counts.completed}
          description="Successfully completed"
          accent="text-emerald-700"
        />
        <SummaryCard
          label="Overdue"
          value={counts.overdue}
          description="Past their due date"
          accent="text-rose-700"
        />
      </section>

      {/* Timeline content */}
      <section className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_2px_8px_rgba(15,23,42,0.025)]">
        {/* Filters */}
        <div className="border-b border-slate-100 p-4 sm:p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-slate-950">
                  All commitments
                </h2>

                {selectedMember && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-violet-100 bg-violet-50/70 px-2.5 py-0.5 text-xs font-medium text-violet-700">
                    <User size={12} aria-hidden="true" />
                    {selectedMember.name}
                  </span>
                )}
              </div>

              <p className="mt-1 text-xs leading-5 text-slate-500">
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
                    className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 sm:text-sm ${
                      selected
                        ? "bg-violet-50 text-violet-800 ring-1 ring-inset ring-violet-200"
                        : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    {formatStatus(option)}
                    <span
                      className={`rounded-md px-1.5 py-0.5 text-[10px] tabular-nums sm:text-[11px] ${
                        selected
                          ? "bg-violet-100 text-violet-600"
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
        </div>

        {/* Error state */}
        {error && (
          <div
            role="alert"
            className="m-4 flex flex-col gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 sm:m-5 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="flex items-start gap-3">
              <AlertCircle
                size={19}
                className="mt-0.5 shrink-0 text-rose-700"
                aria-hidden="true"
              />
              <div>
                <p className="text-sm font-semibold text-rose-900">
                  Unable to load timeline
                </p>
                <p className="mt-1 break-words text-xs leading-5 text-rose-800">
                  {error}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setRetryKey((value) => value + 1)}
              className="shrink-0 self-start rounded-lg border border-rose-200 bg-white px-3 py-2 text-xs font-semibold text-rose-800 hover:bg-rose-100 sm:self-center"
            >
              Try again
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading ? (
          <div className="space-y-4 p-5 sm:p-6" role="status">
            <span className="sr-only">Loading commitments</span>
            {[1, 2, 3].map((row) => (
              <div
                key={row}
                className="flex animate-pulse items-start gap-4 border-b border-slate-100 pb-5 last:border-0"
              >
                <div className="size-11 shrink-0 rounded-xl bg-slate-100" />
                <div className="min-w-0 flex-1 space-y-3 pt-1">
                  <div className="h-4 w-2/5 rounded bg-slate-100" />
                  <div className="h-3 w-3/5 rounded bg-slate-100" />
                  <div className="h-3 w-1/3 rounded bg-slate-100" />
                </div>
              </div>
            ))}
          </div>
        ) : !selectedFamilyId ? (
          <EmptyState filtered={false} />
        ) : visibleItems.length === 0 ? (
          <EmptyState filtered={filter !== "all" && memberItems.length > 0} />
        ) : (
          <>
            {/* Desktop table heading */}
            <div className="hidden grid-cols-[minmax(0,1fr)_140px_130px] gap-4 border-b border-slate-100 bg-slate-50/70 px-6 py-3 text-[11px] font-semibold uppercase tracking-[0.09em] text-slate-500 md:grid">
              <span>Commitment</span>
              <span>Status</span>
              <span>Priority</span>
            </div>

            <div className="divide-y divide-slate-100">
              {visibleItems.map((item) => (
                <article
                  key={item.id}
                  className="grid gap-4 px-4 py-4 transition-colors hover:bg-slate-50/70 sm:px-5 sm:py-5 md:grid-cols-[minmax(0,1fr)_140px_130px] md:items-center md:gap-4 md:px-6"
                >
                  <div className="flex min-w-0 items-start gap-3 sm:gap-4">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-600 ring-1 ring-inset ring-violet-100 sm:size-11">
                      <CalendarDays size={20} aria-hidden="true" />
                    </div>

                    <div className="min-w-0 flex-1">
                      <h3 className="break-words text-sm font-semibold leading-5 text-slate-900 sm:text-[15px]">
                        {item.title}
                      </h3>

                      {item.description && (
                        <p className="mt-1 break-words text-xs leading-5 text-slate-500 sm:text-sm">
                          {item.description}
                        </p>
                      )}

                      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-500">
                        {item.familyMember && (
                          <span className="inline-flex items-center gap-1.5">
                            <UserRound
                              size={14}
                              aria-hidden="true"
                            />
                            <span className="break-words">
                              {item.familyMember}
                            </span>
                          </span>
                        )}

                        <span className="inline-flex items-center gap-1.5">
                          <Clock3 size={14} aria-hidden="true" />
                          Due {formatDate(item.dueDate)}
                        </span>
                      </div>

                      {/* Mobile badges */}
                      <div className="mt-3 flex flex-wrap gap-2 md:hidden">
                        <span
                          className={`rounded-lg px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset ${statusStyles[item.status]}`}
                        >
                          {formatStatus(item.status)}
                        </span>

                        <span
                          className={`rounded-lg px-2.5 py-1 text-[11px] font-semibold ${priorityStyles[item.priority]}`}
                        >
                          {formatStatus(item.priority)} priority
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Desktop status */}
                  <div className="hidden md:block">
                    <span
                      className={`inline-flex w-fit rounded-lg px-2.5 py-1.5 text-xs font-semibold ring-1 ring-inset ${statusStyles[item.status]}`}
                    >
                      {formatStatus(item.status)}
                    </span>
                  </div>

                  {/* Desktop priority */}
                  <div className="hidden md:block">
                    <span
                      className={`inline-flex w-fit rounded-lg px-2.5 py-1.5 text-xs font-semibold ${priorityStyles[item.priority]}`}
                    >
                      {formatStatus(item.priority)}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}

        {/* Footer */}
        {!loading && !error && selectedFamilyId && visibleItems.length > 0 && (
          <div className="flex flex-col gap-1.5 border-t border-slate-100 bg-slate-50/50 px-4 py-3.5 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <span>
              Showing{" "}
              <strong className="font-semibold text-slate-700">
                {visibleItems.length}
              </strong>{" "}
              of {memberItems.length} commitments
            </span>
            <span>Sorted according to your timeline data</span>
          </div>
        )}
      </section>
    </main>
  );
}