import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HomePage from "../HomePage";

const dashboardApi = vi.hoisted(() => ({
  useFamily: vi.fn(),
  getPriorities: vi.fn(),
  getUpcomingCommitments: vi.fn(),
  getExpenseSummary: vi.fn(),
  getExpenses: vi.fn(),
  getDocuments: vi.fn(),
}));

vi.mock("../../context/FamilyContext", () => ({ useFamily: dashboardApi.useFamily }));
vi.mock("../../services/api/dashboard", () => ({
  getPriorities: dashboardApi.getPriorities,
  getUpcomingCommitments: dashboardApi.getUpcomingCommitments,
}));
vi.mock("../../services/api/expenses", () => ({
  getExpenseSummary: dashboardApi.getExpenseSummary,
  getExpenses: dashboardApi.getExpenses,
}));
vi.mock("../../services/api/documents", () => ({ getDocuments: dashboardApi.getDocuments }));

describe("judge household dashboard scenario", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    dashboardApi.useFamily.mockReturnValue({
      selectedFamilyId: "nair-family",
      selectedMemberId: null,
      members: [],
    });
    dashboardApi.getPriorities.mockResolvedValue([
      { title: "CBC test", priority: "HIGH", reason: "Needed before Doctor Review" },
    ]);
    dashboardApi.getUpcomingCommitments.mockResolvedValue([
      {
        id: "bill-1", family_id: "nair-family", member_id: null,
        title: "KSEB Electricity Bill", due_date: "2026-10-18", status: "PENDING",
      },
      {
        id: "deadline-1", family_id: "nair-family", member_id: null,
        title: "Student registration deadline", due_date: "2026-10-16", status: "PENDING",
      },
    ]);
    dashboardApi.getExpenseSummary.mockResolvedValue({ total: 3050, transaction_count: 2 });
    dashboardApi.getExpenses.mockResolvedValue([
      { id: "grocery-1", description: "Groceries", amount: 1850, category: "GROCERIES", date: "2026-10-13" },
    ]);
    dashboardApi.getDocuments.mockResolvedValue([]);
  });

  it("shows the selected household's current bill, medical priority, deadline, and expense", async () => {
    render(<HomePage />);
    await waitFor(() => expect(dashboardApi.getPriorities).toHaveBeenCalledWith("nair-family"));

    expect(await screen.findByText("Groceries")).toBeTruthy();
    expect(screen.getByText("CBC test")).toBeTruthy();
    expect(screen.getByText("KSEB Electricity Bill")).toBeTruthy();
    expect(screen.getByText("Student registration deadline")).toBeTruthy();
  });
});
