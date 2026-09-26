import { apiRequest } from "./client";

export interface Expense {
  merchant: string;
  id: string;
  description: string;
  amount: number;
  category: string;
  date: string;
  family_member?: string;
}

export interface ExpenseCreateInput {
  description: string;
  amount: number;
  category: string;
  date: string;
  family_member?: string;
}

export interface ExpenseSummary {
  total: number;
  by_category: Record<string, number>;
  transaction_count: number;
}

export async function getExpenses(): Promise<Expense[]> {
  return apiRequest<Expense[]>("/api/v1/expenses");
}

export async function addExpense(input: ExpenseCreateInput): Promise<Expense> {
  return apiRequest<Expense>("/api/v1/expenses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function getExpenseSummary(): Promise<ExpenseSummary> {
  return apiRequest<ExpenseSummary>("/api/v1/expenses/summary");
}