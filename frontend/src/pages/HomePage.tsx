/**
 * HomePage
 *
 * Provides the main dashboard for the Family Context application.
 */

import { useEffect, useState } from "react";

import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import StatusBadge from "../components/ui/StatusBadge";
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
import {getDocuments} from "../services/api/documents";

export default function HomePage() {
  const { selectedFamilyId } = useFamily();

  const [upcomingItems, setUpcomingItems] = useState<Commitment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expenseTotal, setExpenseTotal] = useState<number | null>(null);
  const [recentExpenses, setRecentExpenses] = useState<Expense[]>([]);
  const [documentCount, setDocumentCount] = useState<number | null>(null);
  const [priorities, setPriorities] = useState<Priority[]>([]);

  useEffect(() => {
    if (!selectedFamilyId) {
      setUpcomingItems([]);
      setLoading(false);
      return;
    }

    const loadDashboard = async () => {
      try {
        setLoading(true);
        setError(null);

        const commitments = await getUpcomingCommitments(selectedFamilyId);
        const expenseSummary = await getExpenseSummary(selectedFamilyId);
        const expenses = await getExpenses(selectedFamilyId);
        const documents = await getDocuments(selectedFamilyId);
        const priorityItems = await getPriorities(selectedFamilyId);
        setUpcomingItems(commitments);
        setExpenseTotal(expenseSummary.total);
        setRecentExpenses(expenses.slice(0, 3)); // Get the latest 3 expenses
        setDocumentCount(documents.length); // Set the document count
        setPriorities(priorityItems); // Set the priorities
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unable to load dashboard data.",
        );
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, [selectedFamilyId]);

  const pendingCount = upcomingItems.filter(
    (item) => item.status === "PENDING",
  ).length;

  return (
    <div>
      <PageHeader
        title="Good morning, Family"
        description="Here's what's happening with your family today."
      />

      {/* Summary Cards */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm text-slate-500">Upcoming</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {loading ? "..." : upcomingItems.length}
          </p>
          <p className="mt-1 text-sm text-slate-500">family commitments</p>
        </Card>

        <Card>
          <p className="text-sm text-slate-500">Pending</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {loading ? "..." : pendingCount}
          </p>
          <p className="mt-1 text-sm text-slate-500">things need attention</p>
        </Card>

        <Card>
          <p className="text-sm text-slate-500">This Month</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {expenseTotal === null
              ? "..."
              : `₹${expenseTotal.toLocaleString("en-IN")}`}
          </p>
          <p className="mt-1 text-sm text-slate-500">total expenses</p>
        </Card>

        <Card>
          <p className="text-sm text-slate-500">Documents</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{documentCount === null ? "..." : documentCount}</p>
          <p className="mt-1 text-sm text-slate-500">family documents</p>
        </Card>
      </section>

      {/* Dashboard Content */}
      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Upcoming Commitments */}
        <Card>
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900">Upcoming</h2>
            <p className="mt-1 text-sm text-slate-500">
              Important things coming up.
            </p>
          </div>

          {error && (
            <div
              role="alert"
              className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </div>
          )}

          {loading ? (
            <p className="text-sm text-slate-500">Loading commitments...</p>
          ) : upcomingItems.length === 0 ? (
            <p className="text-sm text-slate-500">No upcoming commitments.</p>
          ) : (
            <div className="space-y-4">
              {upcomingItems.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-4 rounded-lg border border-slate-100 p-4"
                >
                  <div className="min-w-0">
                    <h3 className="font-medium text-slate-900">{item.title}</h3>

                    <p className="mt-1 text-sm text-slate-500">
                      {item.due_date ?? "No due date"}
                    </p>
                  </div>

                  <StatusBadge status={item.status} />
                </div>
              ))}
            </div>
          )}
        </Card>

                {/* Priority Items */}
        <Card>
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900">
              Priority Items
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Things that may need attention.
            </p>
          </div>

          {priorities.length === 0 ? (
            <p className="text-sm text-slate-500">
              No priority items.
            </p>
          ) : (
            <div className="space-y-4">
              {priorities.map((priority) => (
                <div
                  key={priority.title}
                  className="rounded-lg border border-slate-100 p-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <h3 className="font-medium text-slate-900">
                      {priority.title}
                    </h3>

                    <StatusBadge status={priority.priority} />
                  </div>

                  <p className="mt-2 text-sm text-slate-500">
                    {priority.reason}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Recent Expenses */}
        <Card>
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900">
              Recent Expenses
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Latest family spending.
            </p>
          </div>

          <div className="space-y-4">
            {recentExpenses.length === 0 ? (
              <p className="text-sm text-slate-500">No recent expenses.</p>
            ) : (
              <div className="space-y-4">
                {recentExpenses.map((expense) => (
                  <div
                    key={expense.id}
                    className="flex items-center justify-between gap-4 rounded-lg border border-slate-100 p-4"
                  >
                    <div>
                      <h3 className="font-medium text-slate-900">
                        {expense.description}
                      </h3>

                      <p className="mt-1 text-sm text-slate-500">
                        {expense.date}
                      </p>
                    </div>

                    <p className="font-semibold text-slate-900">
                      ₹{expense.amount.toLocaleString("en-IN")}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}
