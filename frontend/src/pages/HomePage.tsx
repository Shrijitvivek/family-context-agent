/**
 * HomePage.tsx
 * Family Context — responsive family dashboard
 * Updated with modern design system and complete member filter context support.
 */

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { useFamily } from "../context/FamilyContext";
import {
  getPriorities,
  getUpcomingCommitments,
  type Commitment,
  type Priority,
} from "../services/api/dashboard";
import {
  getExpenseSummary,
  getExpenses,
  type Expense,
} from "../services/api/expenses";
import { getDocuments } from "../services/api/documents";

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
  | "user";

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
  };

  return <svg {...shared}>{drawings[name]}</svg>;
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatDate(value?: string | null) {
  if (!value) return "Date not specified";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function getGreeting() {
  const hour = new Date().getHours();

  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function getExpenseIcon(description?: string): IconName {
  if (!description) return "wallet";
  const text = description.toLowerCase();

  if (/grocery|groceries|supermarket|shopping/.test(text)) return "cart";
  if (/medicine|medical|doctor|hospital|health/.test(text)) return "medical";
  if (/fuel|petrol|diesel|transport/.test(text)) return "fuel";
  if (/food|restaurant|lunch|dinner/.test(text)) return "food";

  return "wallet";
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

function SectionHeading({
  icon,
  tone = "violet",
  title,
  description,
  count,
}: {
  icon: IconName;
  tone?: "violet" | "blue" | "green" | "amber" | "rose" | "slate";
  title: string;
  description: string;
  count?: number;
}) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <IconTile icon={icon} tone={tone} />
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-[15px] font-semibold tracking-[-0.025em] text-slate-950 sm:text-base">
            {title}
          </h2>
          {count !== undefined && count > 0 && (
            <span className="inline-flex min-w-5 items-center justify-center rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
              {count}
            </span>
          )}
        </div>
        <p className="mt-0.5 text-xs leading-5 text-slate-500 sm:text-[13px]">
          {description}
        </p>
      </div>
    </div>
  );
}

function SummaryCard({
  icon,
  tone,
  label,
  value,
  caption,
  loading,
}: {
  icon: IconName;
  tone: "violet" | "blue" | "green" | "amber" | "rose";
  label: string;
  value: string | number;
  caption: string;
  loading: boolean;
}) {
  return (
    <Surface className="group p-4 transition duration-200 hover:border-slate-300 hover:shadow-[0_8px_28px_rgba(15,23,42,0.055)] sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-slate-500">{label}</p>
          <p
            className={`mt-3 break-words text-[26px] font-semibold leading-none tracking-[-0.055em] text-slate-950 sm:text-[29px] ${
              loading ? "animate-pulse text-slate-300" : ""
            }`}
          >
            {loading ? "—" : value}
          </p>
        </div>
        <IconTile icon={icon} tone={tone} size="lg" />
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-500">{caption}</p>
    </Surface>
  );
}

function StatusPill({ status }: { status: string }) {
  const value = status.toUpperCase();

  const tone =
    value === "PENDING"
      ? "border-amber-200 bg-amber-50 text-amber-800"
      : ["COMPLETED", "DONE", "PAID"].includes(value)
        ? "border-emerald-200 bg-emerald-50 text-emerald-800"
        : "border-slate-200 bg-slate-50 text-slate-600";

  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-full border px-2.5 py-1 text-[11px] font-medium ${tone}`}
    >
      {value.charAt(0) + value.slice(1).toLowerCase()}
    </span>
  );
}

function EmptyState({
  icon,
  title,
  description,
}: {
  icon: IconName;
  title: string;
  description: string;
}) {
  return (
    <div className="flex min-h-36 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-5 py-7 text-center">
      <IconTile icon={icon} tone="slate" size="lg" />
      <p className="mt-3 text-sm font-semibold text-slate-800">{title}</p>
      <p className="mt-1 max-w-xs text-xs leading-5 text-slate-500">
        {description}
      </p>
    </div>
  );
}

function LoadingRows({ rows = 3 }: { rows?: number }) {
  return (
    <div className="divide-y divide-slate-100" aria-label="Loading">
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="flex animate-pulse items-center gap-3 py-4">
          <div className="size-10 shrink-0 rounded-xl bg-slate-100" />
          <div className="min-w-0 flex-1 space-y-2">
            <div className="h-3 w-2/5 rounded bg-slate-100" />
            <div className="h-3 w-3/5 rounded bg-slate-100" />
          </div>
          <div className="h-3 w-12 rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}

export default function HomePage() {
  const { selectedFamilyId, selectedMemberId, members } = useFamily();

  const [upcomingItems, setUpcomingItems] = useState<Commitment[]>([]);
  const [priorities, setPriorities] = useState<Priority[]>([]);
  const [recentExpenses, setRecentExpenses] = useState<Expense[]>([]);
  const [expenseTotal, setExpenseTotal] = useState<number | null>(null);
  const [documentCount, setDocumentCount] = useState<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  const selectedMember = members.find(
    (member) => member.id === selectedMemberId,
  );

  useEffect(() => {
    let cancelled = false;

    if (!selectedFamilyId) {
      setUpcomingItems([]);
      setPriorities([]);
      setRecentExpenses([]);
      setExpenseTotal(null);
      setDocumentCount(null);
      setError(null);
      setLoading(false);
      return;
    }

    async function loadDashboard() {
      setLoading(true);
      setError(null);

      try {
        const familyId = selectedFamilyId!;

        const [commitments, summary, expenses, documents, priorityItems] =
          await Promise.all([
            getUpcomingCommitments(familyId, selectedMemberId),
            getExpenseSummary(familyId, selectedMemberId),
            getExpenses(familyId, selectedMemberId),
            getDocuments(familyId, selectedMemberId),
            getPriorities(familyId),
          ]);

        if (cancelled) return;

        // Keep shared commitments along with selected member commitments
        const visibleCommitments = selectedMemberId
          ? commitments.filter(
              (item) =>
                item.member_id === selectedMemberId ||
                item.member_id == null,
            )
          : commitments;

        // Keep unassigned expenses along with member-specific expenses
        const visibleExpenses = selectedMemberId
          ? expenses.filter(
              (expense) =>
                expense.member_id === selectedMemberId ||
                expense.member_id == null,
            )
          : expenses;

        setUpcomingItems(visibleCommitments);
        setExpenseTotal(Number(summary.total));
        setRecentExpenses(visibleExpenses.slice(0, 4));
        setDocumentCount(documents.length);
        setPriorities(priorityItems);
      } catch (err) {
        if (cancelled) return;

        setError(
          err instanceof Error
            ? err.message
            : "Something went wrong while loading your dashboard.",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [selectedFamilyId, selectedMemberId, retryKey]);

  const pendingCount = upcomingItems.filter(
    (item) => item.status.toUpperCase() === "PENDING",
  ).length;

  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <main className="mx-auto w-full max-w-[1600px] space-y-5 pb-8 sm:space-y-6">
      {/* Welcome hero header */}
      <header
        className="relative isolate overflow-hidden rounded-2xl bg-slate-100"
        style={{
          backgroundImage: `
            linear-gradient(
              90deg,
              rgba(238, 231, 231, 0.96) 0%,
              rgba(255,255,255,0.88) 38%,
              rgba(255,255,255,0.46) 65%,
              rgba(255,255,255,0.08) 100%
            ),
            url("https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=2000&q=85")
          `,
          backgroundSize: "cover",
          backgroundPosition: "center 48%",
        }}
      >
        <div className="flex min-h-[220px] flex-col justify-center px-5 py-7 sm:min-h-[230px] sm:px-8 sm:py-8 lg:min-h-[245px] lg:px-10">
          <div className="max-w-2xl">
            <div className="mb-4 flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.15em] text-slate-600 sm:text-xs">
              <span className="size-1.5 rounded-full bg-emerald-500" />
              {selectedMember ? `${selectedMember.name}'s Overview` : "Family Overview"}
              <span className="text-slate-400">/</span>
              <span>{today}</span>
            </div>

            <h1 className="text-3xl font-bold leading-tight tracking-[-0.055em] text-slate-950 sm:text-4xl lg:text-[42px]">
              {getGreeting()}
              {selectedMember ? `, ${selectedMember.name}` : ", family"}.{" "}
              <span aria-hidden="true">👋</span>
            </h1>

            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-700 sm:text-base sm:leading-7">
              {selectedMember
                ? `Here's what's happening on ${selectedMember.name}'s schedule, including personal expenses and shared commitments.`
                : "One place to keep track of what matters at home, from upcoming commitments to shared expenses and important records."}
            </p>

            <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/75 px-3.5 py-2 text-xs font-medium text-slate-700 shadow-sm backdrop-blur-md">
              <Icon name="sparkles" size={16} className="text-violet-600" />
              {selectedMember
                ? `Viewing data for ${selectedMember.name}`
                : "Your family, all in one place"}
            </div>
          </div>
        </div>
      </header>

      {/* Error state */}
      {error && (
        <div
          role="alert"
          className="flex flex-col gap-3 rounded-xl border border-rose-200 bg-rose-50/80 px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="flex items-start gap-3">
            <Icon
              name="alert"
              size={20}
              className="mt-0.5 shrink-0 text-rose-700"
            />
            <div>
              <p className="text-sm font-semibold text-rose-900">
                Dashboard data couldn't be loaded
              </p>
              <p className="mt-1 break-words text-xs leading-5 text-rose-800">
                {error}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setRetryKey((value) => value + 1)}
            className="inline-flex shrink-0 items-center justify-center gap-2 self-start rounded-lg border border-rose-200 bg-white px-3 py-2 text-xs font-semibold text-rose-800 transition hover:bg-rose-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 sm:self-center"
          >
            <Icon name="refresh" size={15} />
            Try again
          </button>
        </div>
      )}

      {/* Summary cards */}
      <section
        aria-label="Family summary"
        className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4"
      >
        <SummaryCard
          icon="calendar"
          tone="violet"
          label="Upcoming commitments"
          value={upcomingItems.length}
          caption={selectedMember ? "Visible member commitments" : "Scheduled family commitments"}
          loading={loading}
        />

        <SummaryCard
          icon="check"
          tone="green"
          label="Pending items"
          value={pendingCount}
          caption="Commitments awaiting completion"
          loading={loading}
        />

        <SummaryCard
          icon="wallet"
          tone="rose"
          label="Recorded expenses"
          value={expenseTotal === null ? "—" : formatCurrency(expenseTotal)}
          caption={selectedMember ? `${selectedMember.name}'s total expenses` : "Total family expenses"}
          loading={loading}
        />

        <SummaryCard
          icon="file"
          tone="blue"
          label="Family documents"
          value={documentCount ?? 0}
          caption="Documents available to this family"
          loading={loading}
        />
      </section>

      {/* Main dashboard grid */}
      <section
        aria-label="Family dashboard details"
        className="grid grid-cols-1 items-start gap-4 xl:grid-cols-2 xl:gap-5"
      >
        {/* Upcoming commitments */}
        <Surface className="p-4 sm:p-5 lg:p-6">
          <div className="mb-4">
            <SectionHeading
              icon="calendar"
              title="Upcoming commitments"
              description={
                selectedMember
                  ? `Commitments for ${selectedMember.name}`
                  : "What's on your family's schedule."
              }
              count={loading ? undefined : upcomingItems.length}
            />
          </div>

          {loading ? (
            <LoadingRows rows={3} />
          ) : upcomingItems.length === 0 ? (
            <EmptyState
              icon="calendar"
              title="Your schedule is clear"
              description="When commitments are added, you'll find them here."
            />
          ) : (
            <div className="divide-y divide-slate-100">
              {upcomingItems.slice(0, 5).map((item, index) => (
                <article
                  key={item.id}
                  className="group flex items-center gap-3 rounded-xl px-2 py-3.5 transition-colors hover:bg-slate-50 sm:gap-4"
                >
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-600 ring-1 ring-inset ring-slate-200/70">
                    <span className="text-xs font-semibold tabular-nums">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                  </div>

                  <div className="min-w-0 flex-1">
                    <h3 className="break-words text-sm font-semibold leading-5 text-slate-900">
                      {item.title}
                    </h3>
                    <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
                      <Icon name="clock" size={13} />
                      {formatDate(item.due_date)}
                    </p>
                  </div>

                  <div className="flex shrink-0 items-center gap-2">
                    <StatusPill status={item.status} />
                    <Icon
                      name="chevron"
                      size={17}
                      className="text-slate-300 transition-colors group-hover:text-violet-600"
                    />
                  </div>
                </article>
              ))}
            </div>
          )}

          {!loading && upcomingItems.length > 5 && (
            <p className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
              Showing 5 of {upcomingItems.length} commitments.
            </p>
          )}
        </Surface>

        {/* Priority items */}
        <Surface className="p-4 sm:p-5 lg:p-6">
          <div className="mb-4">
            <SectionHeading
              icon="flag"
              tone="rose"
              title="Priority items"
              description="Things that may need your attention."
              count={loading ? undefined : priorities.length}
            />
          </div>

          {loading ? (
            <LoadingRows rows={3} />
          ) : priorities.length === 0 ? (
            <EmptyState
              icon="check"
              title="Nothing needs attention"
              description="Priority items will appear here when your dashboard identifies them."
            />
          ) : (
            <div className="divide-y divide-slate-100">
              {priorities.slice(0, 5).map((priority, index) => (
                <article
                  key={`${priority.title}-${index}`}
                  className="group flex items-start gap-3 rounded-xl px-2 py-3.5 transition-colors hover:bg-slate-50"
                >
                  <IconTile
                    icon="flag"
                    tone={index === 0 ? "rose" : "slate"}
                    size="md"
                  />

                  <div className="min-w-0 flex-1">
                    <h3 className="break-words text-sm font-semibold leading-5 text-slate-900">
                      {priority.title}
                    </h3>
                    <p className="mt-1 break-words text-xs leading-5 text-slate-500">
                      {priority.reason}
                    </p>
                  </div>

                  <div className="flex shrink-0 items-center gap-2">
                    <StatusPill status={priority.priority} />
                    <Icon
                      name="chevron"
                      size={17}
                      className="mt-1 text-slate-300 transition-colors group-hover:text-violet-600"
                    />
                  </div>
                </article>
              ))}
            </div>
          )}

          {!loading && priorities.length > 5 && (
            <p className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
              Showing 5 of {priorities.length} priority items.
            </p>
          )}
        </Surface>

        {/* Recent Expenses section */}
        <Surface className="p-4 sm:p-5 lg:p-6 xl:col-span-2">
          <div className="mb-4">
            <SectionHeading
              icon="wallet"
              tone="blue"
              title="Recent expenses"
              description={
                selectedMember
                  ? `Recent spending for ${selectedMember.name} and shared expenses.`
                  : "Latest household spending."
              }
              count={loading ? undefined : recentExpenses.length}
            />
          </div>

          {loading ? (
            <LoadingRows rows={3} />
          ) : recentExpenses.length === 0 ? (
            <EmptyState
              icon="wallet"
              title="No recent expenses"
              description="Transactions will appear here once household spending is recorded."
            />
          ) : (
            <div className="divide-y divide-slate-100">
              {recentExpenses.map((expense) => (
                <article
                  key={expense.id}
                  className="flex items-center justify-between gap-4 py-3.5 px-2 transition-colors hover:bg-slate-50 rounded-xl"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <IconTile
                      icon={getExpenseIcon(expense.description || expense.merchant)}
                      tone="blue"
                      size="md"
                    />
                    <div className="min-w-0">
                      <h3 className="break-words text-sm font-semibold leading-5 text-slate-900">
                        {expense.description || expense.merchant || expense.category}
                      </h3>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {formatDate(expense.date)}
                        {expense.family_member ? ` · Paid by ${expense.family_member}` : ""}
                      </p>
                    </div>
                  </div>

                  <p className="shrink-0 text-sm font-semibold tabular-nums text-slate-950">
                    {formatCurrency(expense.amount)}
                  </p>
                </article>
              ))}
            </div>
          )}
        </Surface>
      </section>
    </main>
  );
}