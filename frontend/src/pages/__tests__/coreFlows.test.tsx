import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HomePage from "../HomePage";

const api = vi.hoisted(() => ({
  useFamily: vi.fn(),
  getPriorities: vi.fn(),
  getUpcomingCommitments: vi.fn(),
  getExpenseSummary: vi.fn(),
  getExpenses: vi.fn(),
  getDocuments: vi.fn(),
}));

vi.mock("../../context/FamilyContext", () => ({ useFamily: api.useFamily }));
vi.mock("../../services/api/dashboard", () => ({
  getPriorities: api.getPriorities,
  getUpcomingCommitments: api.getUpcomingCommitments,
}));
vi.mock("../../services/api/expenses", () => ({
  getExpenseSummary: api.getExpenseSummary,
  getExpenses: api.getExpenses,
}));
vi.mock("../../services/api/documents", () => ({ getDocuments: api.getDocuments }));

describe("HomePage backend data", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.useFamily.mockReturnValue({
      selectedFamilyId: "family-1",
      selectedMemberId: null,
      members: [{ id: "member-1", name: "Asha Nair" }],
    });
    api.getPriorities.mockResolvedValue([
      { title: "Backend attention item", priority: "HIGH", reason: "Due soon" },
    ]);
    api.getUpcomingCommitments.mockResolvedValue([
      {
        id: "commitment-1",
        family_id: "family-1",
        member_id: null,
        title: "Backend electricity commitment",
        amount: 3240,
        due_date: "2026-10-18",
        status: "PENDING",
      },
    ]);
    api.getExpenseSummary.mockResolvedValue({ total: 3240, transaction_count: 1 });
    api.getExpenses.mockResolvedValue([
      {
        id: "expense-1",
        title: "Groceries at Lulu",
        merchant: "Lulu",
        description: "Backend grocery expense",
        amount: 1850,
        category: "GROCERIES",
        date: "2026-10-13",
        member_id: null,
      },
    ]);
    api.getDocuments.mockResolvedValue([]);
  });

  it("requests dashboard data for the selected family without loading priorities", async () => {
    render(<HomePage />);

    await waitFor(() => {
      expect(api.getPriorities).not.toHaveBeenCalled();
      expect(api.getUpcomingCommitments).toHaveBeenCalledWith("family-1", null);
      expect(api.getExpenseSummary).toHaveBeenCalledWith("family-1", null);
      expect(api.getExpenses).toHaveBeenCalledWith("family-1", null);
      expect(api.getDocuments).toHaveBeenCalledWith("family-1", null);
    });
    expect(await screen.findByText("₹3,240.00")).toBeTruthy();
    expect(await screen.findByText("Backend grocery expense")).toBeTruthy();
  });

  it("renders commitments without displaying dynamically updated priorities", async () => {
    render(<HomePage />);

    await screen.findByText("₹3,240.00");
    expect.soft(screen.queryByText("Backend electricity commitment")).toBeTruthy();
    expect.soft(screen.queryByText("Backend attention item")).toBeNull();
  });

  it("shows the runtime date and highlights its calendar day", async () => {
    render(<HomePage />);

    const today = new Date();
    const expectedHeader = new Intl.DateTimeFormat("en-IN", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    })
      .format(today)
      .toUpperCase();
    await screen.findByText("₹3,240.00");
    expect.soft(screen.queryByText(expectedHeader)).toBeTruthy();

    const selectedCalendarDay = document.querySelector(
      ".bg-violet-600.text-white",
    );
    expect.soft(selectedCalendarDay?.textContent).toBe(String(today.getDate()));
  });

  it("does not display demonstration expenses when the backend has none", async () => {
    api.getExpenses.mockResolvedValue([]);
    render(<HomePage />);

    await screen.findByText("Family documents");
    expect.soft(screen.queryByText("Medical - Consultation")).toBeNull();
    expect.soft(screen.queryByText("Groceries")).toBeNull();
    expect.soft(screen.queryByText("Electricity Bill")).toBeNull();
  });

  it("shows a visible error when a dashboard request fails", async () => {
    api.getUpcomingCommitments.mockRejectedValue(new Error("Backend unavailable"));
    render(<HomePage />);

    await waitFor(() => expect(api.getUpcomingCommitments).toHaveBeenCalled());
    expect(await screen.findByRole("alert")).toBeTruthy();
  });

  it("does not retain the previous family's data when the next load fails", async () => {
    const { rerender } = render(<HomePage />);
    expect(await screen.findByText("Backend grocery expense")).toBeTruthy();

    api.useFamily.mockReturnValue({
      selectedFamilyId: "family-2",
      selectedMemberId: null,
      members: [],
    });
    api.getUpcomingCommitments.mockRejectedValueOnce(new Error("Backend unavailable"));
    rerender(<HomePage />);

    await waitFor(() => expect(api.getUpcomingCommitments).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Backend grocery expense")).toBeNull();
  });
});
