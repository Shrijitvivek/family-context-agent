import { useState } from "react";

import {
  confirmDocument,
  type ConfirmedCommitment,
  type DocumentConfirmationPayload,
  type DocumentResponse,
} from "../../services/api/documents";

interface ExtractionConfirmationProps {
  document: DocumentResponse;
  familyId: string;
  onConfirmed: (commitment: ConfirmedCommitment) => void;
}

type ReviewFields = {
  commitment_type: string;
  title: string;
  category: string;
  description: string;
  amount: string;
  start_date: string;
  due_date: string;
  priority: string;
};

function getInitialFields(document: DocumentResponse): ReviewFields {
  const data = document.extracted_data ?? {};
  const value = (key: string) => data[key] == null ? "" : String(data[key]);
  return {
    commitment_type: value("commitment_type") || "BILL",
    title: value("title"),
    category: value("category"),
    description: value("description"),
    amount: value("amount"),
    start_date: value("start_date"),
    due_date: value("due_date"),
    priority: value("priority") || "MEDIUM",
  };
}

export default function ExtractionConfirmation({
  document,
  familyId,
  onConfirmed,
}: ExtractionConfirmationProps) {
  const [fields, setFields] = useState(() => getInitialFields(document));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = (key: keyof ReviewFields, value: string) => {
    setFields((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const payload: DocumentConfirmationPayload = {
      family_id: familyId,
      member_id: document.uploaded_by_member_id,
      commitment_type: fields.commitment_type,
      title: fields.title.trim(),
      category: fields.category.trim() || null,
      description: fields.description.trim() || null,
      amount: fields.amount ? Number(fields.amount) : null,
      start_date: fields.start_date || null,
      due_date: fields.due_date || null,
      priority: fields.priority,
    };

    try {
      const commitment = await confirmDocument(document.id, payload);
      onConfirmed(commitment);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to confirm this document. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass = "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900";

  return (
    <form onSubmit={handleSubmit} className="mt-4 space-y-3 border-t border-slate-200 pt-4">
      <h3 className="text-sm font-semibold text-slate-900">Review extracted information</h3>
      <label className="block text-xs font-medium text-slate-700">
        Commitment type
        <select aria-label="Commitment type" value={fields.commitment_type} onChange={(event) => update("commitment_type", event.target.value)} className={inputClass}>
          {["BILL", "APPOINTMENT", "LAB_TEST", "HOME_TASK", "TASK", "EDUCATION", "DEADLINE", "RENEWAL"].map((type) => <option key={type} value={type}>{type.replaceAll("_", " ")}</option>)}
        </select>
      </label>
      <label className="block text-xs font-medium text-slate-700">
        Title
        <input aria-label="Title" required maxLength={200} value={fields.title} onChange={(event) => update("title", event.target.value)} className={inputClass} />
      </label>
      <label className="block text-xs font-medium text-slate-700">
        Category
        <input aria-label="Category" maxLength={50} value={fields.category} onChange={(event) => update("category", event.target.value)} className={inputClass} />
      </label>
      <label className="block text-xs font-medium text-slate-700">
        Description
        <textarea aria-label="Description" maxLength={2000} value={fields.description} onChange={(event) => update("description", event.target.value)} className={inputClass} />
      </label>
      <label className="block text-xs font-medium text-slate-700">
        Amount
        <input aria-label="Amount" type="number" min="0.01" step="0.01" value={fields.amount} onChange={(event) => update("amount", event.target.value)} className={inputClass} />
      </label>
      <label className="block text-xs font-medium text-slate-700">
        Start date
        <input aria-label="Start date" type="date" value={fields.start_date} onChange={(event) => update("start_date", event.target.value)} className={inputClass} />
      </label>
      <label className="block text-xs font-medium text-slate-700">
        Due date
        <input aria-label="Due date" type="date" value={fields.due_date} onChange={(event) => update("due_date", event.target.value)} className={inputClass} />
      </label>
      <label className="block text-xs font-medium text-slate-700">
        Priority
        <select aria-label="Priority" value={fields.priority} onChange={(event) => update("priority", event.target.value)} className={inputClass}>
          {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((priority) => <option key={priority} value={priority}>{priority}</option>)}
        </select>
      </label>
      {error && <p role="alert" className="text-sm text-rose-700">Confirmation failed: {error}</p>}
      <button type="submit" disabled={submitting || !fields.title.trim()} className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60">
        {submitting ? "Confirming…" : "Confirm details"}
      </button>
    </form>
  );
}
