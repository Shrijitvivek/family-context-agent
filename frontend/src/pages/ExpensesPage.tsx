import type { Expense } from "../types/domain";
import { CalendarDays, CircleDollarSign, UserRound } from "lucide-react";

const sampleExpenses: Expense[] = [
  {
    id: "expense-groceries",
    merchant: "Grocery Shopping",
    amount: 2450,
    category: "Groceries",
    description: "Weekly household groceries",
    date: "2026-09-27T10:15:00",
    familyMember: "Mom",
  },
  {
    id: "expense-pharmacy",
    merchant: "Neighborhood Pharmacy",
    amount: 680,
    category: "Healthcare",
    description: "Prescription refill",
    date: "2026-09-26T16:40:00",
    familyMember: "Dad",
  },
  {
    id: "expense-electricity",
    merchant: "Electricity Bill",
    amount: 1850,
    category: "Utilities",
    description: "September power bill",
    date: "2026-09-22T09:00:00",
    familyMember: "Family",
  },
  {
    id: "expense-school-supplies",
    merchant: "School Supplies",
    amount: 1240,
    category: "Education",
    description: "Notebooks and stationery",
    date: "2026-09-20T14:25:00",
    familyMember: "Aarav",
  },
];

export default function ExpensesPage() {
  const total = sampleExpenses.reduce((sum, item) => sum + item.amount, 0);

  const currency = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  });

  return (
    <main className="mx-auto w-full max-w-6xl px-5 py-8 sm:px-8 sm:py-10">
      <header className="flex flex-col gap-5 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-semibold text-teal-700">Household spending</p>
          <h1 className="text-3xl font-semibold text-slate-950">Expenses</h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">Recent household spending at a glance.</p>
        </div>
        <div className="flex items-center gap-3 border-l-2 border-teal-600 pl-4 sm:min-w-52">
          <CircleDollarSign aria-hidden="true" className="shrink-0 text-teal-700" size={22} />
          <div>
            <p className="text-xs font-semibold text-slate-500">Total expenses</p>
            <p className="mt-0.5 text-2xl font-semibold tabular-nums text-slate-950">{currency.format(total)}</p>
          </div>
        </div>
      </header>

      <section aria-label="Recent expenses" className="mt-7">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">Recent transactions</h2>
          <span className="text-xs font-medium text-slate-500">{sampleExpenses.length} entries</span>
        </div>
        <div className="hidden grid-cols-[minmax(0,1fr)_7rem_7.5rem_8.5rem] gap-3 border-y border-slate-200 bg-slate-50 px-4 py-2.5 text-xs font-semibold text-slate-500 sm:grid">
          <span>Expense</span><span>Category</span><span>Date</span><span className="text-right">Amount</span>
        </div>
        <div className="divide-y divide-slate-200 border-y border-slate-200">
          {sampleExpenses.map((item) => (
            <article className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-3 px-1 py-4 transition-colors hover:bg-slate-50 sm:grid-cols-[minmax(0,1fr)_7rem_7.5rem_8.5rem] sm:gap-3 sm:px-4" key={item.id}>
              <div className="min-w-0">
                <h3 className="break-words text-sm font-semibold text-slate-950">{item.merchant || item.category}</h3>
                {item.description && <p className="mt-1 text-sm leading-5 text-slate-600">{item.description}</p>}
                {item.familyMember && <p className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 sm:hidden"><UserRound aria-hidden="true" size={13} />{item.familyMember}</p>}
              </div>
              <span className="hidden w-fit rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700 sm:inline-flex">{item.category}</span>
              <span className="hidden items-center gap-1.5 text-sm text-slate-600 sm:inline-flex"><CalendarDays aria-hidden="true" size={14} />{new Date(item.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span>
              <div className="row-span-2 flex flex-col items-end gap-1 sm:row-span-1">
                <span className="text-sm font-semibold tabular-nums text-slate-950">{currency.format(item.amount)}</span>
                <span className="text-xs text-slate-500 sm:hidden">{new Date(item.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span>
                <span className="text-xs text-slate-500 sm:hidden">{item.category}{item.familyMember ? ` · ${item.familyMember}` : ""}</span>
              </div>
              <span className="hidden text-xs text-slate-500 sm:block">{item.familyMember ? `Paid by ${item.familyMember}` : ""}</span>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}