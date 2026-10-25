/**
 * HomePage.tsx
 * Family Context — responsive family dashboard
 * Updated with an Unsplash family photo background and first-name slicing.
 */

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

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
import { getTimeline } from "../services/api/timeline";
import type { Commitment as TimelineCommitment } from "../types/domain";

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
  actionText,
  onAction,
}: {
  icon: IconName;
  tone?: "violet" | "blue" | "green" | "amber" | "rose" | "slate";
  title: string;
  actionText?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex min-w-0 items-center gap-3">
        <IconTile icon={icon} tone={tone} size="sm" />
        <h2 className="text-[15px] font-semibold tracking-[-0.025em] text-slate-950 sm:text-base">
          {title}
        </h2>
      </div>
      {actionText && (
        <button
          type="button"
          onClick={onAction}
          className="rounded-lg px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}

export default function HomePage() {
  const { selectedFamilyId, selectedMemberId, members } = useFamily();
  const navigate = useNavigate();
  const [calendarMonth, setCalendarMonth] = useState(() => new Date());

  const [upcomingItems, setUpcomingItems] = useState<Commitment[]>([]);
  const [timelineItems, setTimelineItems] = useState<TimelineCommitment[]>([]);
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

  // Extract only the first name of the selected member if available
  const firstName = selectedMember?.name ? selectedMember.name.split(" ")[0] : null;
  const now = new Date();
  const greeting = now.getHours() < 12 ? "morning" : now.getHours() < 17 ? "afternoon" : "evening";
  const todayLabel = now.toLocaleDateString("en-IN", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  }).toUpperCase();
  const todayKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  const monthStart = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), 1);
  const monthDays = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 0).getDate();
  const calendarOffset = monthStart.getDay();
  const monthLabel = calendarMonth.toLocaleDateString("en-IN", { month: "long", year: "numeric" });
  const commitmentsForCalendar = upcomingItems.filter((item) => item.due_date).map((item) => {
    const date = new Date(item.due_date!);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  });
  const visiblePriorities = priorities.slice(0, 4);
  const activityItems = [
    ...recentExpenses.map((expense) => ({
      key: `expense-${expense.id}`, title: "Expense recorded", detail: expense.description || expense.category,
      date: expense.date ? new Date(expense.date) : null, amount: expense.amount,
    })),
    ...upcomingItems.slice(0, 4).map((item) => ({
      key: `commitment-${item.id}`, title: "Commitment", detail: item.title,
      date: item.due_date ? new Date(item.due_date) : null, amount: null as number | null,
    })),
  ].sort((a, b) => (b.date?.getTime() ?? 0) - (a.date?.getTime() ?? 0)).slice(0, 4);
  const relativeDate = (value: Date | null) => {
    if (!value || Number.isNaN(value.getTime())) return "Date unavailable";
    const days = Math.floor((new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime() - new Date(value.getFullYear(), value.getMonth(), value.getDate()).getTime()) / 86400000);
    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    if (days > 1) return `${days} days ago`;
    if (days === -1) return "Tomorrow";
    return `In ${Math.abs(days)} days`;
  };

  useEffect(() => {
    let cancelled = false;

    if (!selectedFamilyId) {
      setUpcomingItems([]);
      setTimelineItems([]);
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
        const [commitments, summary, expenses, documents, priorityItems, timeline] =
          await Promise.all([
            getUpcomingCommitments(familyId, selectedMemberId),
            getExpenseSummary(familyId, selectedMemberId),
            getExpenses(familyId, selectedMemberId),
            getDocuments(familyId, selectedMemberId),
            getPriorities(familyId),
            getTimeline(familyId),
          ]);

        if (cancelled) return;

        const visibleCommitments = selectedMemberId
          ? commitments.filter(
              (item) =>
                item.member_id === selectedMemberId || item.member_id == null,
            )
          : commitments;

        const visibleExpenses = selectedMemberId
          ? expenses.filter(
              (expense) =>
                expense.member_id === selectedMemberId ||
                expense.member_id == null,
            )
          : expenses;

        setUpcomingItems(visibleCommitments);
        // Home-page tasks are personal: exclude unassigned/shared family commitments.
        const personalTimelineItems = selectedMemberId
          ? timeline.items.filter((item) => item.memberId === selectedMemberId)
          : timeline.items.filter((item) => item.memberId != null);
        setTimelineItems(personalTimelineItems);
        setExpenseTotal(Number(summary.total));
        setRecentExpenses(visibleExpenses.slice(0, 3));
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

  // Upcoming commitments are future-dated, unfinished items in the next 7 days.
  // Today's commitments are counted separately under Today's tasks.
  const upcomingNext7Days = upcomingItems
    .filter((item) => {
      if (!item.due_date) return false;
      const due = new Date(item.due_date);
      if (Number.isNaN(due.getTime())) return false;
      const dueDay = new Date(due.getFullYear(), due.getMonth(), due.getDate());
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const nextWeek = new Date(today);
      nextWeek.setDate(nextWeek.getDate() + 7);
      const status = String(item.status ?? "").toUpperCase();
      return dueDay > today && dueDay <= nextWeek &&
        status !== "COMPLETED" && status !== "CANCELLED";
    })
    .sort((a, b) => new Date(a.due_date!).getTime() - new Date(b.due_date!).getTime());

  // Show only personal tasks that are overdue, critical/urgent, or due today.
  const todayTasks = timelineItems
    .filter((item) => {
      const status = String(item.status ?? "").toLowerCase();
      const priority = String(item.priority ?? "").toLowerCase();
      const due = item.dueDate ? new Date(item.dueDate) : null;
      const hasValidDueDate = Boolean(due && !Number.isNaN(due.getTime()));
      const isDueToday = Boolean(
        hasValidDueDate &&
        due!.getFullYear() === now.getFullYear() &&
        due!.getMonth() === now.getMonth() &&
        due!.getDate() === now.getDate()
      );
      const isOverdue = status === "overdue" || Boolean(
        hasValidDueDate &&
        new Date(due!.getFullYear(), due!.getMonth(), due!.getDate()) <
          new Date(now.getFullYear(), now.getMonth(), now.getDate()) &&
        status !== "completed" &&
        status !== "cancelled"
      );
      const isCritical = ["critical", "urgent"].includes(priority);
      return status !== "completed" && status !== "cancelled" &&
        (isOverdue || isCritical || isDueToday);
    })
    .sort((a, b) => {
      const rank = (item: TimelineCommitment) => {
        const status = String(item.status ?? "").toLowerCase();
        const priority = String(item.priority ?? "").toLowerCase();
        if (status === "overdue") return 0;
        if (["critical", "urgent"].includes(priority)) return 1;
        return 2;
      };
      const rankDifference = rank(a) - rank(b);
      if (rankDifference !== 0) return rankDifference;
      return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
    });

  return (
    <main className="mx-auto w-full max-w-[1600px] space-y-5 pb-8 sm:space-y-6 font-sans">
      {/* Welcome hero header with Unsplash family photo background */}
      <header
        className="relative isolate overflow-hidden rounded-2xl bg-slate-100 shadow-sm border border-slate-200/60"
        style={{
          backgroundImage: `
            linear-gradient(
              90deg,
              rgba(255, 255, 255, 0.95) 0%,
              rgba(255, 255, 255, 0.90) 38%,
              rgba(255, 255, 255, 0.65) 65%,
              rgba(255, 255, 255, 0.25) 100%
            ),
            url("https://images.unsplash.com/photo-1511895426328-dc8714191300?auto=format&fit=crop&w=2000&q=85")
          `,
          backgroundSize: "cover",
          backgroundPosition: "center 40%",
        }}
      >
        <div className="flex min-h-[220px] flex-col justify-between px-6 py-6 sm:min-h-[230px] sm:px-8 lg:min-h-[245px] lg:px-10">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-500 tracking-wider">
              {todayLabel}
            </span>
          </div>

          <div className="max-w-2xl">
            <h1 className="text-3xl font-bold tracking-[-0.055em] text-slate-950 sm:text-4xl lg:text-[40px]">
              Good {greeting}, {firstName ? firstName : "family"} 👋
            </h1>
            <p className="mt-2 max-w-lg text-sm text-slate-600 sm:text-base leading-relaxed">
              Stay on top of what matters. Keep track of commitments, expenses
              and important documents — all in one place.
            </p>
          </div>

          <div>
            <button
              type="button"
              onClick={() => navigate("/timeline")}
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white shadow hover:bg-slate-800 transition"
            >
              View today's plan
              <Icon name="arrow-right" size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* Summary cards row */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Surface className="p-5 flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-500">Today's tasks</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
              {loading ? "—" : todayTasks.length}
            </p>
            <p className="mt-1 text-xs text-slate-500 font-medium">
              Overdue, critical, or due today
            </p>
          </div>
          <IconTile icon="calendar" tone="violet" size="md" />
        </Surface>

        <Surface className="p-5 flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-500">Upcoming commitments</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
              {loading ? "—" : upcomingNext7Days.length}
            </p>
            <p className="mt-1 text-xs text-slate-500 font-medium">
              Scheduled in the next 7 days
            </p>
          </div>
          <IconTile icon="check" tone="green" size="md" />
        </Surface>

        <Surface className="p-5 flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-500">
              Recorded expenses
            </p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
              {expenseTotal === null ? "—" : formatCurrency(expenseTotal)}
            </p>
            <p className="mt-1 text-xs text-slate-500 font-medium">
              {recentExpenses.length} recent transaction{recentExpenses.length === 1 ? "" : "s"} shown below
            </p>
          </div>
          <IconTile icon="wallet" tone="rose" size="md" />
        </Surface>

        <Surface className="p-5 flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-500">
              Family documents
            </p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
              {documentCount ?? 0}
            </p>
            <p className="mt-1 text-xs text-slate-500 font-medium">
              Stored family documents
            </p>
          </div>
          <IconTile icon="file" tone="blue" size="md" />
        </Surface>
      </section>

      {/* Main Grid: Today's tasks, Upcoming commitments, Calendar */}
      <section className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Today's tasks: only tasks assigned to this member, not shared family commitments */}
        <Surface className="p-5">
          <SectionHeading
            icon="calendar"
            title="Today's tasks"
            actionText="View timeline"
            onAction={() => navigate("/timeline")}
          />
          <p className="mt-1 text-[11px] text-slate-500">
            Your overdue, critical, and due-today tasks.
          </p>
          <div className="mt-4 divide-y divide-slate-100">
            {loading ? (
              <p className="py-6 text-center text-xs text-slate-500">Loading your tasks…</p>
            ) : todayTasks.length ? (
              todayTasks.slice(0, 5).map((item) => {
                const due = item.dueDate ? new Date(item.dueDate) : null;
                const status = String(item.status ?? "").toLowerCase();
                const priority = String(item.priority ?? "").toLowerCase();
                const isOverdue = status === "overdue" || Boolean(
                  due && !Number.isNaN(due.getTime()) &&
                  new Date(due.getFullYear(), due.getMonth(), due.getDate()) <
                    new Date(now.getFullYear(), now.getMonth(), now.getDate()) &&
                  status !== "completed" && status !== "cancelled"
                );
                const label = isOverdue ? "Overdue" :
                  ["critical", "urgent"].includes(priority) ? "Critical" : "Due today";
                return pyItemRow({
                  date: due && !Number.isNaN(due.getTime())
                    ? due.toLocaleDateString("en-IN", { day: "2-digit", month: "short" })
                    : "No date",
                  title: item.title,
                  time: label,
                  status: label,
                  color: label === "Overdue" || label === "Critical"
                    ? "bg-rose-500"
                    : "bg-amber-500",
                }, item.id);
              })
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm font-medium text-slate-700">You're all caught up</p>
                <p className="mt-1 text-xs text-slate-500">
                  No personal overdue, critical, or due-today tasks.
                </p>
              </div>
            )}
          </div>
        </Surface>

        {/* Upcoming commitments: future/current commitments, not priority records */}
        <Surface className="p-5">
          <SectionHeading
            icon="calendar"
            tone="violet"
            title="Upcoming commitments"
            actionText="View all"
            onAction={() => navigate("/timeline")}
          />
          <p className="mt-1 text-[11px] text-slate-500">
            What's coming up next for your family.
          </p>
          <div className="mt-4 divide-y divide-slate-100">
            {loading ? (
              <p className="py-6 text-center text-xs text-slate-500">Loading upcoming commitments…</p>
            ) : upcomingItems.filter((item) => {
              if (!item.due_date) return false;
              const due = new Date(item.due_date);
              return !Number.isNaN(due.getTime()) &&
                new Date(due.getFullYear(), due.getMonth(), due.getDate()) >=
                new Date(now.getFullYear(), now.getMonth(), now.getDate()) &&
                item.status.toUpperCase() !== "COMPLETED" &&
                item.status.toUpperCase() !== "CANCELLED";
            }).sort((a, b) => new Date(a.due_date!).getTime() - new Date(b.due_date!).getTime()).slice(0, 5).length ? (
              upcomingItems.filter((item) => {
                if (!item.due_date) return false;
                const due = new Date(item.due_date);
                return !Number.isNaN(due.getTime()) &&
                  new Date(due.getFullYear(), due.getMonth(), due.getDate()) >=
                  new Date(now.getFullYear(), now.getMonth(), now.getDate()) &&
                  item.status.toUpperCase() !== "COMPLETED" &&
                  item.status.toUpperCase() !== "CANCELLED";
              }).sort((a, b) => new Date(a.due_date!).getTime() - new Date(b.due_date!).getTime()).slice(0, 5).map((item) => {
                const due = new Date(item.due_date!);
                const isToday = due.getFullYear() === now.getFullYear() && due.getMonth() === now.getMonth() && due.getDate() === now.getDate();
                return pyItemRow({
                  date: due.toLocaleDateString("en-IN", { day: "2-digit", month: "short" }),
                  title: item.title,
                  time: isToday ? "Today" : due.toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit", hour12: true }),
                  // Show the commitment's priority instead of a generic status like "Pending".
                  status: (() => {
                    const priority = String(
                      (item as Commitment & { priority?: string }).priority ?? "",
                    ).trim().toLowerCase();
                    if (priority === "critical") return "Critical";
                    if (priority === "high") return "High";
                    if (priority === "medium") return "Medium";
                    if (priority === "low") return "Low";
                    return isToday ? "Today" : "No priority";
                  })(),
                  color: (() => {
                    const priority = String(
                      (item as Commitment & { priority?: string }).priority ?? "",
                    ).trim().toLowerCase();
                    if (priority === "critical") return "bg-rose-600";
                    if (priority === "high") return "bg-orange-500";
                    if (priority === "medium") return "bg-amber-500";
                    if (priority === "low") return "bg-emerald-500";
                    return isToday ? "bg-violet-500" : "bg-slate-400";
                  })(),
                }, item.id);
              })
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm font-medium text-slate-700">No upcoming commitments</p>
                <p className="mt-1 text-xs text-slate-500">Future family commitments will appear here.</p>
              </div>
            )}
          </div>
        </Surface>

        {/* Calendar widget */}
        <Surface className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900">{monthLabel}</h3>
            <div className="flex gap-1 text-slate-400">
              <button type="button" aria-label="Previous month" onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() - 1, 1))} className="p-1 hover:bg-slate-100 rounded">‹</button>
              <button type="button" aria-label="Next month" onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 1))} className="p-1 hover:bg-slate-100 rounded">›</button>
            </div>
          </div>
          <div className="grid grid-cols-7 text-center text-[11px] font-medium text-slate-400 mb-2">
            { ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => <span key={day}>{day}</span>) }
          </div>
          <div className="grid grid-cols-7 gap-y-2 text-center text-xs">
            {Array.from({ length: calendarOffset + monthDays }, (_, i) => {
              if (i < calendarOffset) return <div key={`empty-${i}`} />;
              const day = i - calendarOffset + 1;
              const dateKey = `${calendarMonth.getFullYear()}-${String(calendarMonth.getMonth() + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
              const isToday = dateKey === todayKey;
              const hasDot = commitmentsForCalendar.includes(dateKey);
              return <div key={dateKey} className="flex flex-col items-center justify-center">
                <span className={`size-7 flex items-center justify-center rounded-full ${isToday ? "bg-violet-600 text-white font-semibold" : "text-slate-700 hover:bg-slate-100"}`}>{day}</span>
                {hasDot && <span className={`size-1 rounded-full mt-0.5 ${isToday ? "bg-violet-300" : "bg-violet-500"}`} />}
              </div>;
            })}
          </div>
          <p className="mt-3 text-[11px] text-slate-500">Dots indicate dates with commitments from your records.</p>
        </Surface>
      </section>

      {/* Bottom Grid: Recent Expenses, Quick Actions, Recent Activity */}
      <section className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Recent expenses */}
        <Surface className="p-5">
          <SectionHeading
            icon="wallet"
            tone="blue"
            title="Recent expenses"
            actionText="View all"
            onAction={() => navigate("/expenses")}
          />
          <div className="mt-4 divide-y divide-slate-100">
            {recentExpenses.length > 0 ? (
              recentExpenses.map((exp) => (
                <div key={exp.id} className="py-2.5 flex justify-between items-center">
                  <div>
                    <p className="text-xs font-semibold text-slate-900">
                      {exp.description || exp.category}
                    </p>
                    <p className="text-[11px] text-slate-500">
                      {formatDate(exp.date)}
                    </p>
                  </div>
                  <span className="text-xs font-semibold text-slate-900">
                    {formatCurrency(exp.amount)}
                  </span>
                </div>
              ))
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm font-medium text-slate-700">No expenses recorded</p>
                <p className="mt-1 text-xs text-slate-500">New expenses will appear here after they are added.</p>
              </div>
            )}
          </div>
        </Surface>

        {/* Quick actions */}
        <Surface className="p-5">
          <SectionHeading icon="activity" tone="violet" title="Quick actions" />
          <div className="mt-4 grid grid-cols-2 gap-3">
            <button type="button" onClick={() => navigate("/documents")} className="flex flex-col items-center justify-center p-4 rounded-xl border border-blue-100 bg-blue-50/50 hover:bg-blue-100/50 transition text-center">
              <Icon name="upload" size={20} className="text-blue-600 mb-1.5" />
              <span className="text-xs font-semibold text-slate-800">
                Upload document
              </span>
            </button>
            <button type="button" onClick={() => navigate("/chat")} className="flex flex-col items-center justify-center p-4 rounded-xl border border-amber-100 bg-amber-50/50 hover:bg-amber-100/50 transition text-center">
              <Icon name="chat" size={20} className="text-amber-600 mb-1.5" />
              <span className="text-xs font-semibold text-slate-800">
                Ask in chat
              </span>
            </button>
          </div>
        </Surface>

        {/* Recent activity */}
        <Surface className="p-5">
          <SectionHeading
            icon="clock"
            tone="slate"
            title="Recent activity"
            actionText="View all"
            onAction={() => navigate("/timeline")}
          />
          <div className="mt-4 space-y-3 text-xs">
            {activityItems.length ? activityItems.map((item) => (
              <div key={item.key} className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-semibold text-slate-900">{item.title}{item.amount !== null ? ` · ${formatCurrency(item.amount)}` : ""}</p>
                  <p className="text-[11px] text-slate-500 truncate">{item.detail}</p>
                </div>
                <span className="shrink-0 text-[11px] text-slate-400">{relativeDate(item.date)}</span>
              </div>
            )) : (
              <div className="py-8 text-center"><p className="text-sm font-medium text-slate-700">No activity yet</p><p className="mt-1 text-xs text-slate-500">Activity will appear as family records are added.</p></div>
            )}
          </div>
        </Surface>
      </section>
    </main>
  );
}

function pyItemRow(item: any, idx: string | number) {
  return (
    <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
      <div className="flex items-center gap-3">
        <div className="w-10 text-slate-400 font-medium">
          <span className="block text-slate-900 font-semibold">
            {item.date.split(" ")[0]}
          </span>
          <span>{item.date.split(" ")[1]}</span>
        </div>
        <span className={`size-2 rounded-full ${item.color}`} />
        <div>
          <p className="font-semibold text-slate-900">{item.title}</p>
          <p className="text-[11px] text-slate-500">{item.time}</p>
        </div>
      </div>
      <span
        className={`px-2 py-0.5 rounded-md font-semibold text-[10px] ${
          item.status === "Overdue" || item.status === "Critical"
            ? "bg-rose-100 text-rose-700"
            : item.status === "High"
            ? "bg-orange-100 text-orange-700"
            : item.status === "Medium"
            ? "bg-amber-100 text-amber-700"
            : item.status === "Low"
            ? "bg-emerald-100 text-emerald-700"
            : item.status === "Pending"
            ? "bg-amber-100 text-amber-700"
            : "bg-blue-100 text-blue-700"
        }`}
      >
        {item.status}
      </span>
    </div>
  );
}