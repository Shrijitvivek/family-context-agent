import { useMemo, useState } from "react";
import { CalendarDays, UserRound } from "lucide-react";
import type { Commitment, CommitmentStatus } from "../types/domain";

const filters: Array<"all" | CommitmentStatus> = ["all", "pending", "completed", "overdue"];

const statusStyles: Record<CommitmentStatus, string> = {
  pending: "bg-amber-50 text-amber-800 ring-amber-200",
  completed: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  overdue: "bg-rose-50 text-rose-800 ring-rose-200",
  cancelled: "bg-slate-100 text-slate-700 ring-slate-200",
};

const priorityStyles: Record<Commitment["priority"], string> = {
  low: "bg-slate-100 text-slate-700",
  medium: "bg-sky-50 text-sky-800",
  high: "bg-orange-50 text-orange-800",
  urgent: "bg-rose-50 text-rose-800",
};

const sampleItems: Commitment[] = [
  {
    id: "commitment-doctor-visit",
    title: "Doctor appointment",
    familyMember: "Dad",
    dueDate: "2026-09-28T09:00:00",
    status: "pending",
    priority: "high",
    description: "Annual checkup at the family clinic.",
  },
  {
    id: "commitment-school-fee",
    title: "School fee payment",
    familyMember: "Aarav",
    dueDate: "2026-09-30T12:00:00",
    status: "pending",
    priority: "urgent",
    description: "Submit the term fee before the deadline.",
  },
  {
    id: "commitment-lab-test",
    title: "CBC test",
    familyMember: "Mom",
    dueDate: "2026-10-02T08:30:00",
    status: "pending",
    priority: "medium",
    description: "Bring the lab referral form.",
  },
  {
    id: "commitment-insurance",
    title: "Renew health insurance",
    familyMember: "Family",
    dueDate: "2026-09-20T17:00:00",
    status: "overdue",
    priority: "high",
    description: "Review and renew the family policy.",
  },
  {
    id: "commitment-groceries",
    title: "Weekly grocery shopping",
    familyMember: "Mom",
    dueDate: "2026-09-25T18:00:00",
    status: "completed",
    priority: "low",
    description: "Household groceries for the week.",
  },
];

export default function TimelinePage() {
  const [filter, setFilter] = useState<(typeof filters)[number]>("all");

  const visibleItems = useMemo(
    () => (filter === "all" ? sampleItems : sampleItems.filter((item) => item.status === filter)),
    [filter],
  );

  return (
    <main className="mx-auto w-full max-w-6xl px-5 py-8 sm:px-8 sm:py-10">
      <header className="flex flex-col gap-5 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-semibold text-teal-700">Family commitments</p>
          <h1 className="text-3xl font-semibold text-slate-950">Timeline</h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">Keep the next important things visible.</p>
        </div>
        <p className="text-sm text-slate-600"><span className="font-semibold text-slate-950">{visibleItems.length}</span> {visibleItems.length === 1 ? "commitment" : "commitments"}</p>
      </header>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm font-medium text-slate-700">Filter by status</p>
        <div className="inline-flex w-fit max-w-full flex-wrap gap-1 rounded-md border border-slate-200 bg-white p-1" role="group" aria-label="Filter commitments by status">
          {filters.map((option) => {
            const count = option === "all" ? sampleItems.length : sampleItems.filter((item) => item.status === option).length;
            const selected = filter === option;

            return (
              <button
                aria-pressed={selected}
                className={`rounded px-3 py-2 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 ${selected ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"}`}
                key={option}
                onClick={() => setFilter(option)}
                type="button"
              >
                {option[0].toUpperCase() + option.slice(1)} <span className={selected ? "text-slate-300" : "text-slate-400"}>{count}</span>
              </button>
            );
          })}
        </div>
      </div>

      {visibleItems.length === 0 ? (
        <p className="mt-6 rounded-md border border-dashed border-slate-300 px-5 py-10 text-center text-sm text-slate-600">No commitments match this filter.</p>
      ) : (
        <section aria-label="Commitments" className="mt-5 divide-y divide-slate-200 border-y border-slate-200">
          {visibleItems.map((item) => (
            <article className="grid gap-4 px-1 py-5 transition-colors hover:bg-slate-50 sm:grid-cols-[minmax(0,1fr)_9rem_9rem] sm:items-center sm:px-4" key={item.id}>
              <div className="min-w-0">
                <h2 className="break-words text-base font-semibold text-slate-950">{item.title}</h2>
                {item.description && <p className="mt-1 text-sm leading-5 text-slate-600">{item.description}</p>}
                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs font-medium text-slate-500">
                  {item.familyMember && <span className="inline-flex items-center gap-1.5"><UserRound aria-hidden="true" size={14} />{item.familyMember}</span>}
                  <span className="inline-flex items-center gap-1.5"><CalendarDays aria-hidden="true" size={14} />Due {new Date(item.dueDate).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span>
                </div>
              </div>
              <span className={`w-fit rounded px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${statusStyles[item.status]}`}>{item.status[0].toUpperCase() + item.status.slice(1)}</span>
              <span className={`w-fit rounded px-2.5 py-1 text-xs font-semibold ${priorityStyles[item.priority]}`}>{item.priority[0].toUpperCase() + item.priority.slice(1)} priority</span>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}