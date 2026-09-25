import { useEffect, useState } from "react";
import { getExpenses } from "../services/api/expenses";
import type { Expense } from "../services/api/expenses";

export default function ExpensesPage() {
  const [items, setItems] = useState<Expense[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getExpenses()
      .then((response) => {
        setItems(response);
        setTotal(response.reduce((sum, item) => sum + item.amount, 0));
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  return <main className="page-shell"><div className="page-heading"><div><p className="eyebrow">Household spending</p><h1>Expenses</h1><p className="muted">A simple view of where family money is going.</p></div><div className="total-block"><span className="muted">Total</span><strong>${total.toFixed(2)}</strong></div></div>{error && <p className="state-message error">Unable to load expenses: {error}</p>}{!error && items.length === 0 && <p className="state-message">No expenses recorded yet.</p>}<div className="expense-list">{items.map((item) => <article className="expense-row" key={item.id}><div><h2>{item.merchant || item.category}</h2><p className="muted">{item.description || item.category} {item.family_member ? `· ${item.family_member}` : ""}</p></div><div className="expense-amount"><strong>${item.amount.toFixed(2)}</strong><span className="muted">{new Date(item.date).toLocaleDateString()}</span></div></article>)}</div></main>;
}