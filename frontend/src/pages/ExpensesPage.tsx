import { useEffect, useState } from "react";

import {
  CalendarDays,
  CircleDollarSign,
  UserRound,
} from "lucide-react";

import {
  getExpenses,
  getExpenseSummary,
  type Expense,
} from "../services/api/expenses";
import { useFamily } from "../context/FamilyContext";

export default function ExpensesPage() {
  const { selectedFamilyId } = useFamily();

  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedFamilyId) {
      setExpenses([]);
      setTotal(0);
      setLoading(false);
      return;
    }

    const loadExpenses = async () => {
      try {
        setLoading(true);
        setError(null);

        const [expenseData, summary] = await Promise.all([
          getExpenses(selectedFamilyId),
          getExpenseSummary(selectedFamilyId),
        ]);

        setExpenses(expenseData);
        setTotal(summary.total);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load expenses.",
        );
      } finally {
        setLoading(false);
      }
    };

    loadExpenses();
  }, [selectedFamilyId]);

  const currency = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  });

  return (
    <main className="mx-auto w-full max-w-6xl px-5 py-8 sm:px-8 sm:py-10">
      <header className="flex flex-col gap-5 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-semibold text-teal-700">
            Household spending
          </p>

          <h1 className="text-3xl font-semibold text-slate-950">
            Expenses
          </h1>

          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">
            Recent household spending at a glance.
          </p>
        </div>

        <div className="flex items-center gap-3 border-l-2 border-teal-600 pl-4 sm:min-w-52">
          <CircleDollarSign
            aria-hidden="true"
            className="shrink-0 text-teal-700"
            size={22}
          />

          <div>
            <p className="text-xs font-semibold text-slate-500">
              Total expenses
            </p>

            <p className="mt-0.5 text-2xl font-semibold tabular-nums text-slate-950">
              {currency.format(total)}
            </p>
          </div>
        </div>
      </header>

      {error && (
        <div
          role="alert"
          className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {loading ? (
        <div className="mt-7 rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
          Loading expenses...
        </div>
      ) : (
        <section aria-label="Recent expenses" className="mt-7">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">
              Recent transactions
            </h2>

            <span className="text-xs font-medium text-slate-500">
              {expenses.length} entries
            </span>
          </div>

          {expenses.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
              <p className="text-sm text-slate-500">
                No expenses recorded yet.
              </p>
            </div>
          ) : (
            <>
              <div className="hidden grid-cols-[minmax(0,1fr)_7rem_7.5rem_8.5rem] gap-3 border-y border-slate-200 bg-slate-50 px-4 py-2.5 text-xs font-semibold text-slate-500 sm:grid">
                <span>Expense</span>
                <span>Category</span>
                <span>Date</span>
                <span className="text-right">Amount</span>
              </div>

              <div className="divide-y divide-slate-200 border-y border-slate-200">
                {expenses.map((item) => (
                  <article
                    className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-3 px-1 py-4 transition-colors hover:bg-slate-50 sm:grid-cols-[minmax(0,1fr)_7rem_7.5rem_8.5rem] sm:gap-3 sm:px-4"
                    key={item.id}
                  >
                    <div className="min-w-0">
                      <h3 className="break-words text-sm font-semibold text-slate-950">
                        {item.merchant || item.category}
                      </h3>

                      {item.description && (
                        <p className="mt-1 text-sm leading-5 text-slate-600">
                          {item.description}
                        </p>
                      )}

                      {item.family_member && (
                        <p className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 sm:hidden">
                          <UserRound
                            aria-hidden="true"
                            size={13}
                          />
                          {item.family_member}
                        </p>
                      )}
                    </div>

                    <span className="hidden w-fit rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700 sm:inline-flex">
                      {item.category}
                    </span>

                    <span className="hidden items-center gap-1.5 text-sm text-slate-600 sm:inline-flex">
                      <CalendarDays
                        aria-hidden="true"
                        size={14}
                      />
                      {new Date(item.date).toLocaleDateString(
                        "en-IN",
                        {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        },
                      )}
                    </span>

                    <div className="row-span-2 flex flex-col items-end gap-1 sm:row-span-1">
                      <span className="text-sm font-semibold tabular-nums text-slate-950">
                        {currency.format(item.amount)}
                      </span>

                      <span className="text-xs text-slate-500 sm:hidden">
                        {new Date(item.date).toLocaleDateString(
                          "en-IN",
                          {
                            day: "numeric",
                            month: "short",
                          },
                        )}
                      </span>

                      <span className="text-xs text-slate-500 sm:hidden">
                        {item.category}
                        {item.family_member
                          ? ` · ${item.family_member}`
                          : ""}
                      </span>
                    </div>

                    <span className="hidden text-xs text-slate-500 sm:block">
                      {item.family_member
                        ? `Paid by ${item.family_member}`
                        : ""}
                    </span>
                  </article>
                ))}
              </div>
            </>
          )}
        </section>
      )}
    </main>
  );
}