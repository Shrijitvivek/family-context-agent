import type { Commitment, Expense } from "./domain";

export interface TimelineResponse {
	items: Commitment[];
}

export interface ExpenseSummary {
	total: number;
	byCategory: Record<string, number>;
}

export interface ExpensesResponse {
	items: Expense[];
	summary?: ExpenseSummary;
}
