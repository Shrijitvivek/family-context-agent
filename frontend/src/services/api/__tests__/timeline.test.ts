import { beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({ get: vi.fn() }));

vi.mock("../client", () => ({
  apiClient: { get: api.get },
}));

import { getTimeline } from "../timeline";

describe("getTimeline priority cases", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.each([
    { status: "PENDING", inputPriority: "LOW", expected: "low" },
    { status: "PENDING", inputPriority: "MEDIUM", expected: "medium" },
    { status: "PENDING", inputPriority: "HIGH", expected: "high" },
    { status: "PENDING", inputPriority: "CRITICAL", expected: "critical" },
    { status: "OVERDUE", inputPriority: "CRITICAL", expected: "critical" },
  ])(
    "$status with $inputPriority returns $expected",
    async ({ status, inputPriority, expected }) => {
      api.get.mockResolvedValue({
        data: {
          family_id: "family-1",
          start_date: null,
          end_date: null,
          days: [
            {
              day: "2026-10-14",
              commitments: [
                {
                  id: "commitment-1",
                  title: "Test commitment",
                  status,
                  priority: inputPriority,
                },
              ],
            },
          ],
        },
      });

      const result = await getTimeline("family-1");

      expect(result.items[0].priority).toBe(expected);
    },
  );
});
