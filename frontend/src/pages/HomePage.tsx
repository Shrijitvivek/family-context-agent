/**
 * HomePage
 *
 * Provides the main dashboard for the Family Context application.
 *
 * Responsibilities:
 * - Give the family a quick overview of important information.
 * - Display upcoming commitments and recent expenses.
 * - Highlight important family activity.
 * - Provide a foundation for connecting real dashboard data from the API.
 *
 * Note:
 * The data shown here is temporary UI data. It will be replaced with
 * real FastAPI data during frontend-backend integration.
 */

import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import StatusBadge from "../components/ui/StatusBadge";

const upcomingItems = [
  {
    title: "Doctor Appointment",
    member: "Dad",
    date: "Tomorrow",
    status: "Pending",
  },
  {
    title: "School Fee Payment",
    member: "Aarav",
    date: "28 Sep",
    status: "Pending",
  },
  {
    title: "CBC Test",
    member: "Mom",
    date: "30 Sep",
    status: "Pending",
  },
];

const recentExpenses = [
  {
    title: "Grocery Shopping",
    amount: "₹2,450",
    date: "Today",
  },
  {
    title: "Pharmacy",
    amount: "₹680",
    date: "Yesterday",
  },
  {
    title: "Electricity Bill",
    amount: "₹1,850",
    date: "22 Sep",
  },
];

export default function HomePage() {
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
          <p className="mt-2 text-3xl font-bold text-slate-900">3</p>
          <p className="mt-1 text-sm text-slate-500">items this week</p>
        </Card>

        <Card>
          <p className="text-sm text-slate-500">Pending</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">2</p>
          <p className="mt-1 text-sm text-slate-500">things need attention</p>
        </Card>

        <Card>
          <p className="text-sm text-slate-500">This Month</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">₹12,480</p>
          <p className="mt-1 text-sm text-slate-500">total expenses</p>
        </Card>

        <Card>
          <p className="text-sm text-slate-500">Documents</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">8</p>
          <p className="mt-1 text-sm text-slate-500">family documents</p>
        </Card>
      </section>

      {/* Main Dashboard Content */}
      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Upcoming Commitments */}
        <Card>
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Upcoming
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Important things coming up.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {upcomingItems.map((item) => (
              <div
                key={`${item.title}-${item.member}`}
                className="flex items-center justify-between gap-4 rounded-lg border border-slate-100 p-4"
              >
                <div className="min-w-0">
                  <h3 className="font-medium text-slate-900">
                    {item.title}
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    {item.member} · {item.date}
                  </p>
                </div>

                <StatusBadge status={item.status} />
              </div>
            ))}
          </div>
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
            {recentExpenses.map((expense) => (
              <div
                key={`${expense.title}-${expense.date}`}
                className="flex items-center justify-between gap-4 rounded-lg border border-slate-100 p-4"
              >
                <div>
                  <h3 className="font-medium text-slate-900">
                    {expense.title}
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    {expense.date}
                  </p>
                </div>

                <p className="font-semibold text-slate-900">
                  {expense.amount}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}