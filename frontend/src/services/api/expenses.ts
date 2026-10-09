
import { apiClient } from "./client";

export interface Expense {
  id: string;
  title: string;
  merchant: string;
  description: string;
  amount: number;
  category: string;
  date: string;
  member_id: string | null;
  family_member?: string;
}

export interface ExpenseCreateInput {
  family_id: string;
  description: string;
  amount: number;
  category: string;
  expense_date: string;
  member_id?: string | null;
}

export interface ExpenseSummary {
  total: number;
  transaction_count: number;
  category?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export async function getExpenses(
  familyId: string,
  memberId?: string | null,
): Promise<Expense[]> {
  const response = await apiClient.get<
    Array<{
      id: string;
      amount: number | string;
      category: string;
      merchant: string | null;
      description: string | null;
      expense_date: string;
      member_id: string | null;
    }>
  >("/expenses", {
    params: {
      family_id: familyId,
      ...(memberId ? { member_id: memberId } : {}),
    },
  });

  return response.data.map((expense) => ({
    id: expense.id,
    title: expense.merchant ?? expense.category,
    amount: Number(expense.amount),
    category: expense.category,
    merchant: expense.merchant ?? "",
    description: expense.description ?? "",
    date: expense.expense_date,
    member_id: expense.member_id,
  }));
}

export async function addExpense(
  input: ExpenseCreateInput,
): Promise<Expense> {
  const response = await apiClient.post<Expense>("/expenses", input);
  return response.data;
}

export async function getExpenseSummary(
  familyId: string,
  memberId?: string | null,
): Promise<ExpenseSummary> {
  const response = await apiClient.get<ExpenseSummary>(
    "/expenses/summary",
    {
      params: {
        family_id: familyId,
        ...(memberId ? { member_id: memberId } : {}),
      },
    },
  );

  return response.data;
}
