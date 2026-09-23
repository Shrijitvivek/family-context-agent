import { apiClient } from "./client";

export interface Expense {
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
  const response = await apiClient.get<Expense[]>("/expenses");
  return response.data;
}

export async function addExpense(input: ExpenseCreateInput): Promise<Expense> {
  const response = await apiClient.post<Expense>("/expenses", input);
  return response.data;
}

export async function getExpenseSummary(): Promise<ExpenseSummary> {
  const response = await apiClient.get<ExpenseSummary>("/expenses/summary");
  return response.data;
}