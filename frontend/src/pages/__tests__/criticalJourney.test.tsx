import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HomePage from "../HomePage";
import DocumentsPage from "../DocumentsPage";

const api = vi.hoisted(() => ({
  useFamily: vi.fn(),
  getPriorities: vi.fn(),
  getUpcomingCommitments: vi.fn(),
  getExpenseSummary: vi.fn(),
  getExpenses: vi.fn(),
  getDocuments: vi.fn(),
  uploadDocument: vi.fn(),
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
vi.mock("../../services/api/documents", () => ({
  getDocuments: api.getDocuments,
  uploadDocument: api.uploadDocument,
}));

describe("critical dashboard journey UI contracts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.useFamily.mockReturnValue({
      selectedFamilyId: "nair-family",
      selectedMemberId: null,
      members: [],
    });
    api.getPriorities.mockResolvedValue([
      { title: "CBC test", priority: "HIGH", reason: "Prerequisite is complete" },
    ]);
    api.getUpcomingCommitments.mockResolvedValue([
      {
        id: "kseb-1",
        family_id: "nair-family",
        member_id: null,
        title: "KSEB Electricity Bill",
        amount: 3240,
        due_date: "2026-10-18",
        status: "PENDING",
      },
    ]);
    api.getExpenseSummary.mockResolvedValue({ total: 1850, transaction_count: 1 });
    api.getExpenses.mockResolvedValue([
      {
        id: "expense-1",
        description: "Groceries",
        amount: 1850,
        category: "GROCERIES",
        date: "2026-10-13",
        member_id: null,
      },
    ]);
    api.getDocuments.mockResolvedValue([]);
  });

  it("renders current backend household state instead of the October 11 demo dashboard", async () => {
    render(<HomePage />);

    await screen.findByText("Groceries");
    const now = new Date();
    const currentDate = new Intl.DateTimeFormat("en-IN", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(now).toUpperCase();

    expect(screen.getByText(currentDate)).toBeTruthy();
    expect(screen.queryByText("CBC test")).toBeNull();
    expect(screen.getByText("KSEB Electricity Bill")).toBeTruthy();
    expect(screen.queryByText("SUNDAY, 11 OCTOBER 2026")).toBeNull();
    expect(screen.queryByText("KSEB Electricity Bill is due tomorrow")).toBeNull();
  });

  it("offers bill confirmation after a document reaches NEEDS_CONFIRMATION", async () => {
    api.getDocuments.mockResolvedValue([
      {
        id: "bill-doc-1",
        family_id: "nair-family",
        uploaded_by_member_id: null,
        file_name: "kseb-october.pdf",
        processing_status: "NEEDS_CONFIRMATION",
        extracted_data: { title: "KSEB Electricity Bill", amount: "3240.00" },
        created_at: "2026-10-13T00:00:00Z",
        updated_at: "2026-10-13T00:00:00Z",
      },
    ]);
    render(<DocumentsPage />);

    expect(await screen.findByText("kseb-october.pdf")).toBeTruthy();
    await waitFor(() => expect(api.getDocuments).toHaveBeenCalledWith("nair-family", null));
    expect(screen.getByRole("button", { name: /confirm/i })).toBeTruthy();
  });
});
