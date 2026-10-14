import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  CalendarDays,
  CircleDollarSign,
  UserRound,
  ReceiptText,
  RefreshCw,
  Wallet,
  User,
} from "lucide-react";

import {
  getExpenses,
  getExpenseSummary,
  type Expense,
} from "../services/api/expenses";
import { useFamily } from "../context/FamilyContext";

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
  | "arrow-right"
  | "receipt";

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
    receipt: (
      <>
        <path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2L18 3l-2-1-2 1-2-1-2 1-2-1-2 1-2-1Z" />
        <path d="M8 8h8M8 12h8M8 16h5" />
      </>
    ),
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

export default function ExpensesPage() {
  const {
    selectedFamilyId,
    selectedMemberId,
    members,
  } = useFamily();

  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const selectedMember = members.find(
    (member) => member.id === selectedMemberId,
  );

  useEffect(() => {
    if (!selectedFamilyId) {
      setExpenses([]);
      setTotal(0);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;

    const loadExpenses = async () => {
      try {
        setLoading(true);
        setError(null);

        const [expenseData, summary] = await Promise.all([
          getExpenses(selectedFamilyId, selectedMemberId),
          getExpenseSummary(selectedFamilyId, selectedMemberId),
        ]);

        if (cancelled) return;

        const visibleExpenses = selectedMemberId
          ? expenseData.filter(
              (expense) =>
                expense.member_id === selectedMemberId ||
                expense.member_id == null,
            )
          : expenseData;

        const memberNamesById = new Map(
          members.map((member) => [member.id, member.name]),
        );

        setExpenses(
          visibleExpenses.map((expense) => ({
            ...expense,
            family_member: expense.member_id
              ? memberNamesById.get(expense.member_id) ?? undefined
              : undefined,
          })),
        );

        setTotal(Number(summary.total));
      } catch (err) {
        if (cancelled) return;

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load expenses. Please try again.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadExpenses();

    return () => {
      cancelled = true;
    };
  }, [selectedFamilyId, selectedMemberId, retryCount, members]);

  const currency = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  });

  const formatDate = (date: string, includeYear = true) =>
    new Date(date).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      ...(includeYear ? { year: "numeric" } : {}),
    });

  return (
    <main className="mx-auto w-full max-w-[1600px] space-y-5 pb-8 sm:space-y-6 font-sans">
      {/* Page header */}
      <Surface className="p-6 sm:p-8 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-rose-100 bg-rose-50/70 px-3 py-1.5">
            <Wallet aria-hidden="true" size={14} className="text-rose-600" />
            <span className="text-xs font-semibold text-rose-700">
              Household spending
            </span>
          </div>

          <h1 className="text-3xl font-bold tracking-[-0.055em] text-slate-950 sm:text-4xl">
            Expenses
          </h1>

          <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-600">
            {selectedMember
              ? `Expenses for ${selectedMember.name}, including shared expenses.`
              : "Recent household spending at a glance."}
          </p>
        </div>

        {/* Total expenses summary box */}
        <div className="flex items-center gap-4 rounded-2xl border border-slate-200/80 bg-slate-50/50 p-4 sm:min-w-72 sm:p-5">
          <IconTile icon="wallet" tone="rose" size="md" />
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-500">
              {selectedMember ? "Member expenses" : "Total expenses"}
            </p>
            <p className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
              {loading ? "—" : currency.format(total)}
            </p>
          </div>
        </div>
      </Surface>

      {/* Error state */}
      {error && (
        <div
          role="alert"
          className="flex flex-col gap-3 rounded-2xl border border-rose-200 bg-rose-50/70 p-5 sm:flex-row sm:items-center sm:justify-between shadow-sm"
        >
          <div>
            <p className="text-sm font-semibold text-rose-800">
              Unable to load expenses
            </p>
            <p className="mt-1 text-sm text-rose-700">{error}</p>
          </div>
          <button
            type="button"
            onClick={() => setRetryCount((count) => count + 1)}
            className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-xs font-semibold text-rose-700 shadow-sm border border-rose-200 hover:bg-rose-50 transition"
          >
            <RefreshCw size={14} aria-hidden="true" />
            Try again
          </button>
        </div>
      )}

      {/* Recent transactions section */}
      <Surface className="p-5 sm:p-6">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold tracking-tight text-slate-950">
              Recent transactions
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Your household expenses in one place.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {selectedMember && (
              <span className="inline-flex items-center gap-1.5 rounded-xl border border-violet-100 bg-violet-50/70 px-3 py-1 text-xs font-medium text-violet-700">
                <User size={13} aria-hidden="true" />
                Filtered by {selectedMember.name}
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
              <ReceiptText size={13} aria-hidden="true" />
              {expenses.length} {expenses.length === 1 ? "entry" : "entries"}
            </span>
          </div>
        </div>

        {loading ? (
          <div className="space-y-3 py-4">
            {[1, 2, 3, 4].map((item) => (
              <div
                key={item}
                className="h-12 w-full animate-pulse rounded-xl bg-slate-100"
              />
            ))}
          </div>
        ) : !selectedFamilyId ? (
          <div className="rounded-2xl border border-dashed border-slate-200 px-5 py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
              <Wallet size={22} aria-hidden="true" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900">
              Select a family
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Choose a family to view its expenses.
            </p>
          </div>
        ) : expenses.length === 0 && !error ? (
          <div className="rounded-2xl border border-dashed border-slate-200 px-5 py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-50 text-rose-600">
              <ReceiptText size={22} aria-hidden="true" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900">
              No expenses yet
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Household transactions will appear here once recorded.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-200/80">
            {/* Desktop column headings */}
            <div className="hidden grid-cols-[minmax(0,1fr)_9rem_9rem_9rem_9rem] gap-4 border-b border-slate-200/80 bg-slate-50/70 px-5 py-3 text-xs font-semibold text-slate-500 sm:grid">
              <span>Expense</span>
              <span>Category</span>
              <span>Date</span>
              <span>Paid by</span>
              <span className="text-right">Amount</span>
            </div>

            <div className="divide-y divide-slate-100">
              {expenses.map((item) => (
                <div
                  key={item.id}
                  className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 py-3.5 transition hover:bg-slate-50/70 sm:grid-cols-[minmax(0,1fr)_9rem_9rem_9rem_9rem] sm:gap-4 sm:px-5 sm:py-3.5"
                >
                  {/* Expense merchant / description */}
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-900 truncate">
                      {item.merchant || item.category}
                    </p>
                    {item.description && (
                      <p className="text-[11px] text-slate-500 truncate mt-0.5">
                        {item.description}
                      </p>
                    )}
                  </div>

                  {/* Category */}
                  <div className="hidden sm:block">
                    <span className="inline-flex items-center rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-700 uppercase tracking-wide">
                      {item.category}
                    </span>
                  </div>

                  {/* Date */}
                  <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500">
                    <CalendarDays size={13} className="text-slate-400" />
                    <span>{formatDate(item.date)}</span>
                  </div>

                  {/* Payer */}
                  <div className="hidden sm:block text-xs text-slate-600 truncate">
                    {item.family_member ?? "Not assigned"}
                  </div>

                  {/* Amount */}
                  <div className="text-right">
                    <span className="text-xs font-semibold text-slate-900 tabular-nums">
                      {currency.format(item.amount)}
                    </span>
                    <div className="flex items-center justify-end gap-2 text-[11px] text-slate-500 sm:hidden mt-0.5">
                      <span>{formatDate(item.date, false)}</span>
                      {item.family_member && <span>· {item.family_member}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Surface>
    </main>
  );
}