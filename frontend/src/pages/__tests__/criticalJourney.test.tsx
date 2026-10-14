import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  confirmDocument: vi.fn(),
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
  confirmDocument: api.confirmDocument,
}));

describe("critical dashboard journey UI contracts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.useFamily.mockReturnValue({
      families: [{ id: "nair-family", timezone: "Asia/Kolkata" }],
      selectedFamilyId: "nair-family",
      selectedMemberId: null,
      members: [],
    });
    api.getPriorities.mockResolvedValue([
      {
        id: "priority-cbc", commitment_id: "cbc-1", notification_type: "DEPENDENCY",
        title: "CBC test", message: "Prerequisite is complete", priority: "HIGH",
        is_read: false, created_at: "2026-10-14T00:00:00Z",
      },
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
    api.confirmDocument.mockResolvedValue({
      id: "commitment-1",
      title: "KSEB Electricity Bill",
      status: "PENDING",
      due_date: "2026-10-18",
    });
  });

  it("renders current backend household state instead of the October 11 demo dashboard", async () => {
    render(<HomePage />);

    await screen.findByText("Groceries");
    const now = new Date();
    const currentDate = new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(now).toUpperCase();

    expect(screen.getByText(currentDate)).toBeTruthy();
    expect(screen.getByText("CBC test")).toBeTruthy();
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
    expect(screen.getByText("Review extracted information")).toBeTruthy();
    expect((screen.getByLabelText("Title") as HTMLInputElement).value).toBe("KSEB Electricity Bill");
    expect((screen.getByLabelText("Amount") as HTMLInputElement).value).toBe("3240.00");
    expect(screen.getByRole("button", { name: "Confirm details" })).toBeTruthy();
  });

  it("submits reviewed fields to the confirmation API and shows the confirmed result", async () => {
    api.getDocuments.mockResolvedValue([
      {
        id: "bill-doc-1",
        family_id: "nair-family",
        uploaded_by_member_id: "member-1",
        file_name: "kseb-october.pdf",
        processing_status: "NEEDS_CONFIRMATION",
        extracted_data: { title: "KSEB Electricity Bill", amount: "3240.00", due_date: "2026-10-18" },
        created_at: "2026-10-13T00:00:00Z",
        updated_at: "2026-10-13T00:00:00Z",
      },
    ]);
    render(<DocumentsPage />);

    await screen.findByText("kseb-october.pdf");
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "October electricity bill" } });
    fireEvent.change(screen.getByLabelText("Amount"), { target: { value: "3300" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirm details" }));

    await screen.findByRole("status");
    expect(api.confirmDocument).toHaveBeenCalledWith("bill-doc-1", {
      family_id: "nair-family",
      member_id: "member-1",
      commitment_type: "BILL",
      title: "October electricity bill",
      category: null,
      description: null,
      amount: 3300,
      start_date: null,
      due_date: "2026-10-18",
      priority: "MEDIUM",
    });
    expect(screen.getByText("Confirmed: KSEB Electricity Bill")).toBeTruthy();
    await waitFor(() => expect(api.getDocuments).toHaveBeenCalledTimes(2));
  });

  it("shows confirmation failure and keeps reviewed fields available for retry", async () => {
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
    api.confirmDocument.mockRejectedValueOnce(new Error("Database unavailable"));
    render(<DocumentsPage />);

    await screen.findByText("kseb-october.pdf");
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Reviewed electricity bill" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirm details" }));

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText("Confirmation failed: Database unavailable")).toBeTruthy();
    expect((screen.getByLabelText("Title") as HTMLInputElement).value).toBe("Reviewed electricity bill");
    expect(screen.getByRole("button", { name: "Confirm details" })).toBeTruthy();
    expect(screen.queryByText("Confirmed: KSEB Electricity Bill")).toBeNull();
    expect(api.getDocuments).toHaveBeenCalledTimes(1);
  });
});
