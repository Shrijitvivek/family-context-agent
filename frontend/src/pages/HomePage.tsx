
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
import { getDocuments } from "../services/api/documents";

export default function HomePage() {
  const { selectedFamilyId, selectedMemberId, members } = useFamily();

  const [upcomingItems, setUpcomingItems] = useState<Commitment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expenseTotal, setExpenseTotal] = useState<number | null>(null);
  const [recentExpenses, setRecentExpenses] = useState<Expense[]>([]);
  const [documentCount, setDocumentCount] = useState<number | null>(null);
  const [priorities, setPriorities] = useState<Priority[]>([]);

  const selectedMember = members.find(
    (member) => member.id === selectedMemberId,
  );

  useEffect(() => {
    if (!selectedFamilyId) {
      setUpcomingItems([]);
      setRecentExpenses([]);
      setPriorities([]);
      setExpenseTotal(null);
      setDocumentCount(null);
      setLoading(false);
      return;
    }

    let cancelled = false;

    const loadDashboard = async () => {
      setLoading(true);
      setError(null);

      try {
        const [
          commitments,
          expenseSummary,
          expenses,
          documents,
          priorityItems,
        ] = await Promise.all([
          getUpcomingCommitments(selectedFamilyId, selectedMemberId),
          getExpenseSummary(selectedFamilyId, selectedMemberId),
          getExpenses(selectedFamilyId, selectedMemberId),
          getDocuments(selectedFamilyId, selectedMemberId),
          getPriorities(selectedFamilyId),
        ]);

        if (cancelled) return;

        // Include shared commitments when a member is selected.
        const visibleCommitments = selectedMemberId
          ? commitments.filter(
              (item) =>
                item.member_id === selectedMemberId ||
                item.member_id == null,
            )
          : commitments;

        // Include member-specific and unassigned expenses.
        const visibleExpenses = selectedMemberId
          ? expenses.filter(
              (expense) =>
                expense.member_id === selectedMemberId ||
                expense.member_id == null,
            )
          : expenses;

        setUpcomingItems(visibleCommitments);
        setExpenseTotal(Number(expenseSummary.total));
        setRecentExpenses(visibleExpenses.slice(0, 3));
        setDocumentCount(documents.length);
        setPriorities(priorityItems);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load dashboard data.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [selectedFamilyId, selectedMemberId]);

  const pendingCount = upcomingItems.filter(
    (item) => item.status === "PENDING",
  ).length;

  const viewLabel = selectedMember
    ? `${selectedMember.name}'s`
    : "Family";

  return (
    <div>
      <PageHeader
        title={
          selectedMember
            ? `${selectedMember.name}'s Dashboard`
            : "Good morning, Family"
        }
        description={`Here's what's happening with ${viewLabel.toLowerCase()} today.`}
      />

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm text-slate-500">Upcoming</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {loading ? "..." : upcomingItems.length}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            {selectedMember ? "visible commitments" : "family commitments"}
          </p>
        </Card>

        <Card>
          <p className="text-sm text-slate-500">Pending</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {loading ? "..." : pendingCount}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            things need attention
          </p>
        </Card>

        <Card>
          <p className="text-sm text-slate-500">Expenses</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {loading || expenseTotal === null
              ? "..."
              : `₹${expenseTotal.toLocaleString("en-IN")}`}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            {selectedMember ? "selected member's expenses" : "family expenses"}
          </p>
        </Card>

        <Card>
          <p className="text-sm text-slate-500">Documents</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {loading || documentCount === null ? "..." : documentCount}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            family documents
          </p>
        </Card>
      </section>

      {/* Dashboard Content */}
      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Upcoming Commitments */}
        <Card>
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900">
              Upcoming
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Important things coming up.
            </p>
          </div>

          {loading ? (
            <p className="text-sm text-slate-500">
              Loading commitments...
            </p>
          ) : upcomingItems.length === 0 ? (
            <p className="text-sm text-slate-500">
              No upcoming commitments.
            </p>
          ) : (
            <div className="space-y-4">
              {upcomingItems.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-4 rounded-lg border border-slate-100 p-4"
                >
                  <div className="min-w-0">
                    <h3 className="font-medium text-slate-900">
                      {item.title}
                    </h3>
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

          {loading ? (
            <p className="text-sm text-slate-500">Loading priorities...</p>
          ) : priorities.length === 0 ? (
            <p className="text-sm text-slate-500">No priority items.</p>
          ) : (
            <div className="space-y-4">
              {priorities.map((priority, index) => (
                <div
                  key={`${priority.title}-${index}`}
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
              Latest spending.
            </p>
          </div>

          {loading ? (
            <p className="text-sm text-slate-500">Loading expenses...</p>
          ) : recentExpenses.length === 0 ? (
            <p className="text-sm text-slate-500">No recent expenses.</p>
          ) : (
            <div className="space-y-4">
              {recentExpenses.map((expense) => (
                <div
                  key={expense.id}
                  className="flex items-center justify-between gap-4 rounded-lg border border-slate-100 p-4"
                >
                  <div className="min-w-0">
                    <h3 className="font-medium text-slate-900">
                      {expense.description || expense.title}
                    </h3>
                    <p className="mt-1 text-sm text-slate-500">
                      {expense.date}
                    </p>
                  </div>
                  <p className="shrink-0 font-semibold text-slate-900">
                    ₹{expense.amount.toLocaleString("en-IN")}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </section>
    </div>
  );
}
