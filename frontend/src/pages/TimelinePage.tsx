import { useEffect, useMemo, useState } from "react";
import { getTimeline } from "../services/api/timeline";
import type { Commitment, CommitmentStatus } from "../types/domain";

const filters: Array<"all" | CommitmentStatus> = ["all", "pending", "completed", "overdue"];

export default function TimelinePage() {
  const [items, setItems] = useState<Commitment[]>([]);
  const [filter, setFilter] = useState<(typeof filters)[number]>("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTimeline().then((response) => setItems(response.items)).catch((reason: Error) => setError(reason.message));
  }, []);

  const visibleItems = useMemo(
    () => (filter === "all" ? items : items.filter((item) => item.status === filter)),
    [filter, items],
  );

  return (
    <main className="page-shell">
      <div className="page-heading">
        <div><p className="eyebrow">Family commitments</p><h1>Timeline</h1><p className="muted">Keep the next important things visible.</p></div>
        <span className="count-badge">{visibleItems.length} items</span>
      </div>
      <div className="filter-row" aria-label="Timeline filters">
        {filters.map((option) => <button className={filter === option ? "filter-button active" : "filter-button"} key={option} onClick={() => setFilter(option)}>{option[0].toUpperCase() + option.slice(1)}</button>)}
      </div>
      {error && <p className="state-message error">Unable to load commitments: {error}</p>}
      {!error && visibleItems.length === 0 && <p className="state-message">No commitments match this filter.</p>}
      <div className="timeline-list">{visibleItems.map((item) => <article className="timeline-item" key={item.id}><div className={`status-dot ${item.status}`} /><div className="timeline-content"><div className="item-topline"><h2>{item.title}</h2><span className={`priority ${item.priority}`}>{item.priority}</span></div><p className="muted">Due {new Date(item.dueDate).toLocaleDateString()} {item.familyMember ? `· ${item.familyMember}` : ""}</p>{item.description && <p>{item.description}</p>}</div></article>)}</div>
    </main>
  );
}