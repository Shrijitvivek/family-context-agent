export type CommitmentStatus = "pending" | "scheduled" | "in_progress" | "completed" | "overdue" | "cancelled";
export type CommitmentPriority = "low" | "medium" | "high" | "critical";

export interface Commitment {
	id: string;
	title: string;
	dueDate: string;
	status: CommitmentStatus;
	priority: CommitmentPriority | null;
	memberId?: string | null;
	familyMember?: string | null;
	category?: string | null;
	description?: string | null;
}

export interface Expense {
	id: string;
	amount: number;
	category: string;
	merchant?: string | null;
	date: string;
	description?: string | null;
	familyMember?: string | null;
}
