import type { ExpensesResponse } from "../../types/api";
import { apiRequest } from "./client";

export function getExpenses(): Promise<ExpensesResponse> {
	return apiRequest<ExpensesResponse>("/api/v1/expenses");
}
