import { apiClient } from "./client";

export interface Expense {
  title: any;
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

export async function getExpenses(familyId: string): Promise<Expense[]> {
  const response = await apiClient.get<
    Array<{
      id: string;
      amount: number;
      category: string;
      merchant: string | null;
      description: string | null;
      expense_date: string;
      member_id: string | null;
    }>
  >("/expenses", {
    params: {
      family_id: familyId,
    },
  });

  return response.data.map((expense) => ({
    id: expense.id,
    title : expense.merchant ?? expense.category,
    amount: expense.amount,
    category: expense.category,
    merchant: expense.merchant ?? "",
    description: expense.description ?? "",
    date: expense.expense_date,
    family_member: undefined,
  }));
}

export async function addExpense(input: ExpenseCreateInput): Promise<Expense> {
  const response = await apiClient.post<Expense>("/expenses", input);
  return response.data;
}

export async function getExpenseSummary(
  familyId: string,
): Promise<ExpenseSummary> {
  const response = await apiClient.get<ExpenseSummary>("/expenses/summary", {
    params: {
      family_id: familyId,
    },
  });
  return response.data;
}
