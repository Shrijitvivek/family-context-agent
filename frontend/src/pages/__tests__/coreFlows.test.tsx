import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HomePage from "../HomePage";
import { getFamilyCalendarDate } from "../../utils/familyDate";

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
      families: [
        { id: "family-1", timezone: "Asia/Kolkata" },
        { id: "family-2", timezone: "America/Los_Angeles" },
      ],
      selectedFamilyId: "family-1",
      selectedMemberId: null,
      members: [{ id: "member-1", name: "Asha Nair" }],
    });
    api.getPriorities.mockResolvedValue([
      {
        id: "priority-1", commitment_id: "commitment-1", notification_type: "DEADLINE",
        title: "Backend attention item", message: "Due soon", priority: "HIGH",
        is_read: false, created_at: "2026-10-14T00:00:00Z",
      },
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

  it("requests dashboard data for the selected family", async () => {
    render(<HomePage />);

    await waitFor(() => {
      expect(api.getPriorities).toHaveBeenCalledWith("family-1");
      expect(api.getUpcomingCommitments).toHaveBeenCalledWith("family-1", null);
      expect(api.getExpenseSummary).toHaveBeenCalledWith("family-1", null);
      expect(api.getExpenses).toHaveBeenCalledWith("family-1", null);
      expect(api.getDocuments).toHaveBeenCalledWith("family-1", null);
    });
    expect(await screen.findByText("₹3,240.00")).toBeTruthy();
    expect(await screen.findByText("Backend grocery expense")).toBeTruthy();
  });

  it("renders commitment and priority entries returned by the backend", async () => {
    render(<HomePage />);

    await screen.findByText("₹3,240.00");
    expect.soft(screen.queryByText("Backend electricity commitment")).toBeTruthy();
    expect.soft(screen.queryByText("Backend attention item")).toBeTruthy();
  });

  it("shows the runtime date and highlights its calendar day", async () => {
    render(<HomePage />);

    const today = new Date();
    const expectedHeader = new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
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
    const familyDay = new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
      day: "numeric",
    }).format(today);
    expect.soft(selectedCalendarDay?.textContent).toBe(familyDay);
  });

  it("uses the selected family's timezone for the header, month, and selected calendar day", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-12-31T23:30:00.000Z"));
    try {
      const familyContext = {
        families: [
          { id: "family-1", timezone: "Asia/Kolkata" },
          { id: "family-2", timezone: "America/Los_Angeles" },
        ],
        selectedFamilyId: "family-1",
        selectedMemberId: null,
        members: [],
      };
      api.useFamily.mockReturnValue(familyContext);
      const { rerender } = render(<HomePage />);
      await screen.findByText("Backend grocery expense");

      expect(screen.getByText("FRIDAY, 1 JANUARY 2027")).toBeTruthy();
      expect(screen.getByText("January 2027")).toBeTruthy();
      expect(document.querySelector('[aria-current="date"]')?.textContent).toBe("1");

      api.useFamily.mockReturnValue({ ...familyContext, selectedFamilyId: "family-2" });
      rerender(<HomePage />);

      expect(screen.getByText("THURSDAY, 31 DECEMBER 2026")).toBeTruthy();
      expect(await screen.findByText("December 2026")).toBeTruthy();
      expect(document.querySelector('[aria-current="date"]')?.textContent).toBe("31");
    } finally {
      vi.useRealTimers();
    }
  });

  it("falls back to the application's Asia/Kolkata timezone when family timezone is missing or invalid", () => {
    const instant = new Date("2026-12-31T23:30:00.000Z");
    expect(getFamilyCalendarDate(undefined, instant).headerLabel).toBe("FRIDAY, 1 JANUARY 2027");
    expect(getFamilyCalendarDate("Invalid/FamilyZone", instant).monthYearLabel).toBe("January 2027");
  });

  it("does not display demonstration expenses when the backend has none", async () => {
    api.getExpenses.mockResolvedValue([]);
    render(<HomePage />);

    await screen.findByText("Family documents");
    expect.soft(screen.queryByText("Medical - Consultation")).toBeNull();
    expect.soft(screen.queryByText("Groceries")).toBeNull();
    expect.soft(screen.queryByText("Electricity Bill")).toBeNull();
    expect(screen.getByText("No expenses recorded for this household.")).toBeTruthy();
  });

  it("shows a visible error when a dashboard request fails", async () => {
    api.getPriorities.mockRejectedValue(new Error("Backend unavailable"));
    render(<HomePage />);

    await waitFor(() => expect(api.getPriorities).toHaveBeenCalled());
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
    api.getPriorities.mockRejectedValueOnce(new Error("Backend unavailable"));
    rerender(<HomePage />);

    await waitFor(() => expect(api.getPriorities).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Backend grocery expense")).toBeNull();
    expect(await screen.findByRole("alert")).toBeTruthy();
  });

  it("clears prior household data while switching, shows loading/error, and retries with new data", async () => {
    let rejectSecondFamily!: (reason: Error) => void;
    let resolveRetry!: (value: {
      id: string; commitment_id: string; notification_type: string; title: string;
      message: string; priority: string; is_read: boolean; created_at: string;
    }[]) => void;
    let familyBAttempts = 0;

    api.getPriorities.mockImplementation((familyId: string) => {
      if (familyId !== "family-2") return Promise.resolve([{
        id: "priority-a", commitment_id: "commitment-1", notification_type: "DEADLINE",
        title: "Family A attention", message: "Family A reason", priority: "HIGH",
        is_read: false, created_at: "2026-10-14T00:00:00Z",
      }]);
      familyBAttempts += 1;
      if (familyBAttempts === 1) {
        return new Promise((_resolve, reject) => { rejectSecondFamily = reject; });
      }
      return new Promise((resolve) => { resolveRetry = resolve; });
    });
    api.getUpcomingCommitments.mockImplementation((familyId: string) => Promise.resolve([
      {
        id: familyId === "family-2" ? "commitment-b" : "commitment-a",
        family_id: familyId,
        member_id: null,
        title: familyId === "family-2" ? "Family B bill" : "Family A bill",
        due_date: "2026-10-20",
        status: "PENDING",
      },
    ]));
    api.getExpenses.mockImplementation((familyId: string) => Promise.resolve([
      {
        id: familyId === "family-2" ? "expense-b" : "expense-a",
        description: familyId === "family-2" ? "Family B groceries" : "Backend grocery expense",
        amount: 1850,
        category: "GROCERIES",
        date: "2026-10-13",
        member_id: null,
      },
    ]));
    api.getExpenseSummary.mockImplementation((familyId: string) => Promise.resolve({
      total: familyId === "family-2" ? 2900 : 3240,
      transaction_count: 1,
    }));

    const { rerender } = render(<HomePage />);
    expect(await screen.findByText("Backend grocery expense")).toBeTruthy();
    expect(screen.getByText("Family A bill")).toBeTruthy();
    expect(screen.getByText("Family A attention")).toBeTruthy();

    api.useFamily.mockReturnValue({
      selectedFamilyId: "family-2",
      selectedMemberId: null,
      members: [],
    });
    rerender(<HomePage />);

    expect(await screen.findByRole("status")).toBeTruthy();
    expect(screen.queryByText("Backend grocery expense")).toBeNull();
    expect(screen.queryByText("Family A bill")).toBeNull();
    expect(screen.queryByText("Family A attention")).toBeNull();
    await waitFor(() => expect(rejectSecondFamily).toBeTypeOf("function"));
    rejectSecondFamily(new Error("Family B unavailable"));

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText("Family B unavailable")).toBeTruthy();
    expect(screen.queryByText("Backend grocery expense")).toBeNull();
    expect(screen.queryByText("Family A bill")).toBeNull();
    expect(screen.queryByText("Family A attention")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("status")).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
    await waitFor(() => expect(resolveRetry).toBeTypeOf("function"));
    resolveRetry([{
      id: "priority-b", commitment_id: "commitment-b", notification_type: "DEADLINE",
      title: "Family B priority", message: "Family B reason", priority: "HIGH",
      is_read: false, created_at: "2026-10-14T00:00:00Z",
    }]);

    expect(await screen.findByText("Family B groceries")).toBeTruthy();
    expect(screen.getByText("Family B bill")).toBeTruthy();
    expect(screen.getByText("Family B priority")).toBeTruthy();
    expect(screen.queryByText("Backend grocery expense")).toBeNull();
    expect(screen.queryByText("Family A bill")).toBeNull();
    expect(screen.queryByText("Family A attention")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
