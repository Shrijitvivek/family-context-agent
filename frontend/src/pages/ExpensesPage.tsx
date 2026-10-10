import { useEffect, useState } from "react";
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

        // Keep only the selected member's expenses and shared expenses.
        // All Family displays every expense.
        const visibleExpenses = selectedMemberId
          ? expenseData.filter(
              (expense) =>
                expense.member_id === selectedMemberId ||
                expense.member_id == null,
            )
          : expenseData;

        setExpenses(visibleExpenses);
        setTotal(Number(summary.total));
      } catch (err) {
        if (cancelled) return;

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load expenses. Please try again."
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
  }, [selectedFamilyId, selectedMemberId, retryCount]);

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
    <main className="mx-auto w-full max-w-6xl px-4 py-7 sm:px-6 sm:py-9 lg:px-8">
      {/* Page header */}
      <header className="flex flex-col gap-6 border-b border-slate-200/80 pb-7 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-violet-100 bg-violet-50/70 px-3 py-1.5">
            <Wallet
              aria-hidden="true"
              size={14}
              className="text-violet-600"
            />
            <span className="text-xs font-semibold text-violet-700">
              Household spending
            </span>
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
            Expenses
          </h1>

          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500">
            {selectedMember
              ? `Expenses for ${selectedMember.name}, including shared expenses.`
              : "Recent household spending at a glance."}
          </p>
        </div>

        {/* Total expenses */}
        <div className="flex items-center gap-4 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm sm:min-w-64 sm:p-5">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-50/70 text-violet-600 ring-1 ring-inset ring-violet-100/70">
            <CircleDollarSign aria-hidden="true" size={23} />
          </div>

          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-500">
              {selectedMember ? "Member expenses" : "Total expenses"}
            </p>

            <p className="mt-1 text-xl font-bold tracking-tight tabular-nums text-slate-950 sm:text-2xl">
              {loading ? (
                <span
                  aria-label="Loading total"
                  className="inline-block h-7 w-32 animate-pulse rounded-md bg-slate-100"
                />
              ) : (
                currency.format(total)
              )}
            </p>
          </div>
        </div>
      </header>

      {/* Error state */}
      {error && (
        <div
          role="alert"
          className="mt-6 flex flex-col gap-3 rounded-xl border border-rose-200 bg-rose-50/70 p-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <p className="text-sm font-semibold text-rose-800">
              Unable to load expenses
            </p>
            <p className="mt-1 break-words text-sm leading-5 text-rose-700">
              {error}
            </p>
          </div>

          <button
            type="button"
            onClick={() => setRetryCount((count) => count + 1)}
            className="inline-flex w-fit shrink-0 items-center justify-center gap-2 rounded-lg border border-rose-200 bg-white px-3.5 py-2 text-sm font-semibold text-rose-700 transition-colors hover:bg-rose-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 focus-visible:ring-offset-2"
          >
            <RefreshCw size={14} aria-hidden="true" />
            Try again
          </button>
        </div>
      )}

      {/* Recent transactions */}
      <section aria-label="Recent expenses" className="mt-7 sm:mt-8">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold tracking-tight text-slate-900">
              Recent transactions
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Your household expenses in one place.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {selectedMember && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-violet-100 bg-violet-50/70 px-3 py-1.5 text-xs font-medium text-violet-700">
                <User size={13} aria-hidden="true" />
                Filtered by {selectedMember.name}
              </span>
            )}

            <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600">
              <ReceiptText size={13} aria-hidden="true" />
              {expenses.length}{" "}
              {expenses.length === 1 ? "entry" : "entries"}
            </span>
          </div>
        </div>

        {/* Loading state */}
        {loading ? (
          <div
            aria-label="Loading expenses"
            aria-busy="true"
            className="overflow-hidden rounded-2xl border border-slate-200 bg-white"
          >
            <div className="hidden grid-cols-[minmax(0,1fr)_7rem_7.5rem_8.5rem] gap-4 border-b border-slate-100 bg-slate-50/70 px-5 py-3 sm:grid">
              {[1, 2, 3, 4].map((item) => (
                <div
                  key={item}
                  className="h-3 w-16 animate-pulse rounded bg-slate-200"
                />
              ))}
            </div>

            {[1, 2, 3, 4].map((item) => (
              <div
                key={item}
                className="flex items-center justify-between gap-4 border-b border-slate-100 px-4 py-5 last:border-b-0 sm:px-5"
              >
                <div className="flex min-w-0 flex-1 items-center gap-3">
                  <div className="h-10 w-10 shrink-0 animate-pulse rounded-xl bg-slate-100" />

                  <div className="min-w-0 flex-1 space-y-2">
                    <div className="h-4 w-32 max-w-full animate-pulse rounded bg-slate-100" />
                    <div className="h-3 w-48 max-w-full animate-pulse rounded bg-slate-100" />
                  </div>
                </div>

                <div className="h-4 w-20 animate-pulse rounded bg-slate-100" />
              </div>
            ))}
          </div>
        ) : !selectedFamilyId ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
              <Wallet size={22} aria-hidden="true" />
            </div>

            <h3 className="mt-4 text-sm font-semibold text-slate-900">
              Select a family
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              Choose a family to view its expenses.
            </p>
          </div>
        ) : expenses.length === 0 && !error ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50/70 text-violet-600 ring-1 ring-inset ring-violet-100/70">
              <ReceiptText size={22} aria-hidden="true" />
            </div>

            <h3 className="mt-4 text-sm font-semibold text-slate-900">
              No expenses yet
            </h3>

            <p className="mx-auto mt-1 max-w-sm text-sm leading-6 text-slate-500">
              Household transactions will appear here once expenses have been
              recorded.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-sm">
            {/* Desktop column headings */}
            <div className="hidden grid-cols-[minmax(0,1fr)_7rem_7.5rem_8.5rem] gap-4 border-b border-slate-200 bg-slate-50/70 px-5 py-3 text-xs font-semibold text-slate-500 sm:grid">
              <span>Expense</span>
              <span>Category</span>
              <span>Date</span>
              <span className="text-right">Amount</span>
            </div>

            <div className="divide-y divide-slate-100">
              {expenses.map((item) => (
                <article
                  key={item.id}
                  className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-3 px-4 py-4 transition-colors hover:bg-slate-50/70 sm:grid-cols-[minmax(0,1fr)_7rem_7.5rem_8.5rem] sm:gap-4 sm:px-5 sm:py-4"
                >
                  {/* Expense details */}
                  <div className="flex min-w-0 items-start gap-3">
                    <div className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-500 ring-1 ring-inset ring-slate-200/80 sm:flex">
                      <ReceiptText size={18} aria-hidden="true" />
                    </div>

                    <div className="min-w-0">
                      <h3 className="break-words text-sm font-semibold text-slate-900">
                        {item.merchant || item.category}
                      </h3>

                      {item.description && (
                        <p className="mt-1 break-words text-sm leading-5 text-slate-500">
                          {item.description}
                        </p>
                      )}

                      {item.family_member && (
                        <p className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 sm:hidden">
                          <UserRound size={13} aria-hidden="true" />
                          {item.family_member}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Category */}
                  <div className="hidden sm:block">
                    <span className="inline-flex max-w-full items-center rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-600">
                      {item.category}
                    </span>
                  </div>

                  {/* Date */}
                  <div className="hidden items-center gap-1.5 text-sm text-slate-500 sm:flex">
                    <CalendarDays
                      size={14}
                      className="shrink-0 text-slate-400"
                      aria-hidden="true"
                    />
                    <span>{formatDate(item.date)}</span>
                  </div>

                  {/* Amount and mobile metadata */}
                  <div className="row-span-2 flex flex-col items-end gap-1.5 sm:row-span-1">
                    <span className="whitespace-nowrap text-sm font-semibold tabular-nums text-slate-900">
                      {currency.format(item.amount)}
                    </span>

                    <span className="inline-flex items-center gap-1 text-xs text-slate-500 sm:hidden">
                      <CalendarDays size={12} aria-hidden="true" />
                      {formatDate(item.date, false)}
                    </span>

                    <span className="max-w-36 text-right text-xs text-slate-500 sm:hidden">
                      {item.category}
                      {item.family_member
                        ? ` · ${item.family_member}`
                        : ""}
                    </span>
                  </div>

                  {/* Payer */}
                  <span className="hidden text-xs text-slate-500 sm:block">
                    {item.family_member
                      ? `Paid by ${item.family_member}`
                      : "—"}
                  </span>
                </article>
              ))}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between gap-3 border-t border-slate-100 bg-slate-50/50 px-4 py-3 sm:px-5">
              <p className="text-xs text-slate-500">
                Showing {expenses.length}{" "}
                {expenses.length === 1 ? "transaction" : "transactions"}
              </p>

              <p className="text-xs font-medium text-slate-600">
                Total{" "}
                <span className="font-semibold tabular-nums text-slate-900">
                  {currency.format(total)}
                </span>
              </p>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}