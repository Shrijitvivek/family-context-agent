import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const chatApi = vi.hoisted(() => ({
  getChatHistory: vi.fn(),
  sendMessage: vi.fn(),
}));

vi.mock("../../services/api/chat", () => chatApi);

import { useChat } from "../useChat";

describe("useChat history recovery", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("preserves a saved conversation after an unrelated HTTP 400", async () => {
    const key = "family-chat:family-a:all-family";
    localStorage.setItem(key, "conversation-a");
    chatApi.getChatHistory.mockRejectedValueOnce({
      response: {
        status: 400,
        data: { code: "scope_violation", message: "Invalid request scope." },
      },
    });

    const { result } = renderHook(() => useChat("family-a", null));

    await waitFor(() =>
      expect(result.current.error).toBe(
        "Unable to load your previous conversation.",
      ),
    );
    expect(localStorage.getItem(key)).toBe("conversation-a");
  });

  it("clears only a response explicitly identifying a missing conversation", async () => {
    const key = "family-chat:family-a:all-family";
    localStorage.setItem(key, "conversation-a");
    chatApi.getChatHistory.mockRejectedValueOnce({
      response: {
        status: 400,
        data: {
          code: "not_found",
          message: "Conversation was not found.",
          details: { entity: "Conversation" },
        },
      },
    });

    const { result } = renderHook(() => useChat("family-a", null));
    await waitFor(() => expect(result.current.historyLoading).toBe(false));

    expect(localStorage.getItem(key)).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
