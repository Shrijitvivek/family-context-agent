/**
 * HomePage.tsx
 * Family Context — responsive family dashboard
 * Updated with an Unsplash family photo background and first-name slicing.
 */

import { useEffect, useState } from "react";
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

  // Extract only the first name of the selected member if available
  const firstName = selectedMember?.name ? selectedMember.name.split(" ")[0] : null;

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

  const pendingCount = upcomingItems.filter(
    (item) => item.status.toUpperCase() === "PENDING",
  ).length;

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
              SUNDAY, 11 OCTOBER 2026
            </span>
          </div>

          <div className="max-w-2xl">
            <h1 className="text-3xl font-bold tracking-[-0.055em] text-slate-950 sm:text-4xl lg:text-[40px]">
              Good afternoon, {firstName ? firstName : "family"} 👋
            </h1>
            <p className="mt-2 max-w-lg text-sm text-slate-600 sm:text-base leading-relaxed">
              Stay on top of what matters. Keep track of commitments, expenses
              and important documents — all in one place.
            </p>
          </div>

          <div>
            <button
              type="button"
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
            <p className="text-xs font-medium text-slate-500">
              Upcoming commitments
            </p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
              {loading ? "—" : upcomingItems.length}
            </p>
            <p className="mt-1 text-xs text-emerald-600 font-medium">
              +2 from last week
            </p>
          </div>
          <IconTile icon="calendar" tone="violet" size="md" />
        </Surface>

        <Surface className="p-5 flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-500">Pending items</p>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
              {loading ? "—" : pendingCount}
            </p>
            <p className="mt-1 text-xs text-amber-600 font-medium">
              3 high priority
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
            <p className="mt-1 text-xs text-rose-600 font-medium">
              -12% from last month
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
            <p className="mt-1 text-xs text-slate-400 font-medium">
              No new documents
            </p>
          </div>
          <IconTile icon="file" tone="blue" size="md" />
        </Surface>
      </section>

      {/* Main Grid: Today's commitments, Priority items, Calendar */}
      <section className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Today's commitments */}
        <Surface className="p-5">
          <SectionHeading
            icon="calendar"
            title="Today's commitments"
            actionText="View all"
          />
          <div className="mt-4 divide-y divide-slate-100">
            {[
              {
                date: "08 Oct",
                title: "Kavya's term fee",
                time: "All day",
                status: "Overdue",
                color: "bg-rose-500",
              },
              {
                date: "11 Oct",
                title: "KSEB Electricity Bill",
                time: "All day",
                status: "Pending",
                color: "bg-amber-500",
              },
              {
                date: "15 Oct",
                title: "Amma's fasting blood sugar test",
                time: "9:00 AM",
                status: "Upcoming",
                color: "bg-blue-500",
              },
              {
                date: "18 Oct",
                title: "Groceries restock",
                time: "All day",
                status: "Upcoming",
                color: "bg-emerald-500",
              },
            ].map((item, idx) => (
              pyItemRow(item, idx)
            ))}
          </div>
        </Surface>

        {/* Priority items */}
        <Surface className="p-5">
          <SectionHeading
            icon="flag"
            tone="rose"
            title="Priority items"
            actionText="View all"
          />
          <div className="mt-4 space-y-3">
            <div className="flex items-start justify-between p-3 rounded-xl bg-rose-50/50 border border-rose-100">
              <div>
                <p className="text-xs font-semibold text-slate-900">
                  Kavya's term fee is overdue
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Overdue since 8 Oct 2026
                </p>
              </div>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-rose-100 text-rose-700 rounded-md">
                Critical
              </span>
            </div>

            <div className="flex items-start justify-between p-3 rounded-xl bg-amber-50/50 border border-amber-100">
              <div>
                <p className="text-xs font-semibold text-slate-900">
                  KSEB Electricity Bill is due tomorrow
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Due on 11 Oct 2026
                </p>
              </div>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-amber-100 text-amber-700 rounded-md">
                High
              </span>
            </div>

            <div className="flex items-start justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div>
                <p className="text-xs font-semibold text-slate-900">
                  Amma's fasting blood sugar test
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Due in 4 days
                </p>
              </div>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-blue-100 text-blue-700 rounded-md">
                Medium
              </span>
            </div>
          </div>
        </Surface>

        {/* Calendar widget */}
        <Surface className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900">
              October 2026
            </h3>
            <div className="flex gap-1 text-slate-400">
              <button className="p-1 hover:bg-slate-100 rounded">‹</button>
              <button className="p-1 hover:bg-slate-100 rounded">›</button>
            </div>
          </div>
          <div className="grid grid-cols-7 text-center text-[11px] font-medium text-slate-400 mb-2">
            <span>Sun</span>
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span>Sat</span>
          </div>
          <div className="grid grid-cols-7 gap-y-2 text-center text-xs">
            {Array.from({ length: 31 }, (_, i) => {
              const day = i + 1;
              const isSelected = day === 11;
              const hasDot = [1, 3, 15, 18, 21, 22].includes(day);
              return (
                <div key={day} className="flex flex-col items-center justify-center">
                  <span
                    className={`size-7 flex items-center justify-center rounded-full ${
                      isSelected
                        ? "bg-violet-600 text-white font-semibold"
                        : "text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {day}
                  </span>
                  {hasDot && (
                    <span className="size-1 rounded-full bg-violet-500 mt-0.5" />
                  )}
                </div>
              );
            })}
          </div>
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
              <>
                <div className="py-2.5 flex justify-between items-center">
                  <div>
                    <p className="text-xs font-semibold text-slate-900">
                      Medical - Consultation
                    </p>
                    <p className="text-[11px] text-slate-500">10 Oct 2026</p>
                  </div>
                  <span className="text-xs font-semibold text-slate-900">
                    ₹500.00
                  </span>
                </div>
                <div className="py-2.5 flex justify-between items-center">
                  <div>
                    <p className="text-xs font-semibold text-slate-900">
                      Groceries
                    </p>
                    <p className="text-[11px] text-slate-500">8 Oct 2026</p>
                  </div>
                  <span className="text-xs font-semibold text-slate-900">
                    ₹1,250.00
                  </span>
                </div>
                <div className="py-2.5 flex justify-between items-center">
                  <div>
                    <p className="text-xs font-semibold text-slate-900">
                      Electricity Bill
                    </p>
                    <p className="text-[11px] text-slate-500">5 Oct 2026</p>
                  </div>
                  <span className="text-xs font-semibold text-slate-900">
                    ₹2,180.00
                  </span>
                </div>
              </>
            )}
          </div>
        </Surface>

        {/* Quick actions */}
        <Surface className="p-5">
          <SectionHeading icon="activity" tone="violet" title="Quick actions" />
          <div className="mt-4 grid grid-cols-2 gap-3">
            <button className="flex flex-col items-center justify-center p-4 rounded-xl border border-slate-100 bg-slate-50 hover:bg-slate-100 transition text-center">
              <Icon name="calendar" size={20} className="text-violet-600 mb-1.5" />
              <span className="text-xs font-semibold text-slate-800">
                Add commitment
              </span>
            </button>
            <button className="flex flex-col items-center justify-center p-4 rounded-xl border border-emerald-100 bg-emerald-50/50 hover:bg-emerald-100/50 transition text-center">
              <Icon name="wallet" size={20} className="text-emerald-600 mb-1.5" />
              <span className="text-xs font-semibold text-slate-800">
                Add expense
              </span>
            </button>
            <button className="flex flex-col items-center justify-center p-4 rounded-xl border border-blue-100 bg-blue-50/50 hover:bg-blue-100/50 transition text-center">
              <Icon name="upload" size={20} className="text-blue-600 mb-1.5" />
              <span className="text-xs font-semibold text-slate-800">
                Upload document
              </span>
            </button>
            <button className="flex flex-col items-center justify-center p-4 rounded-xl border border-amber-100 bg-amber-50/50 hover:bg-amber-100/50 transition text-center">
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
          />
          <div className="mt-4 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-900">
                  Added expense - ₹2,180.00
                </p>
                <p className="text-[11px] text-slate-500">
                  KSEB Electricity Bill
                </p>
              </div>
              <span className="text-[11px] text-slate-400">2 days ago</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-900">
                  Added commitment
                </p>
                <p className="text-[11px] text-slate-500">
                  KSEB Electricity Bill
                </p>
              </div>
              <span className="text-[11px] text-slate-400">3 days ago</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-900">Uploaded document</p>
              </div>
              <span className="text-[11px] text-slate-400">5 days ago</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-900">Chat session</p>
                <p className="text-[11px] text-slate-500">
                  Discussed upcoming expenses
                </p>
              </div>
              <span className="text-[11px] text-slate-400">5 days ago</span>
            </div>
          </div>
        </Surface>
      </section>
    </main>
  );
}

function pyItemRow(item: any, idx: number) {
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
          item.status === "Overdue"
            ? "bg-rose-100 text-rose-700"
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