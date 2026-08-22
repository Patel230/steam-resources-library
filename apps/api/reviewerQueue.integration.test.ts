import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TrpcContext } from "./_core/context";

const queueDb = vi.hoisted(() => ({
  createReviewerQueueItem: vi.fn(),
  listReviewerQueueItems: vi.fn(),
  decideReviewerQueueItem: vi.fn(),
}));

vi.mock("./db", () => queueDb);

import { appRouter } from "./routers";

function contextFor(role: "admin" | "user" | null): TrpcContext {
  return {
    user: role
      ? {
          id: 31,
          openId: "queue-integration-test",
          name: "Queue Tester",
          email: "queue@example.com",
          loginMethod: "manus",
          role,
          createdAt: new Date(),
          updatedAt: new Date(),
          lastSignedIn: new Date(),
        }
      : null,
    req: {} as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const sourceLead = {
  submitterName: "Public contributor",
  submitterEmail: "contributor@example.com",
  country: "Philippines",
  resourceUrl: "https://example.edu.ph/mathematics/archive",
  resourceTitle: "Example University Mathematics Archive",
  sourceType: "University examination papers",
  notes: "Public archive page with direct downloadable papers.",
};

describe("reviewer queue integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    queueDb.createReviewerQueueItem.mockResolvedValue(42);
    queueDb.listReviewerQueueItems.mockResolvedValue([]);
    queueDb.decideReviewerQueueItem.mockResolvedValue({ id: 42, status: "approved" });
  });

  it("routes a public lead through owner review without an automatic catalog mutation", async () => {
    const publicCaller = appRouter.createCaller(contextFor(null));
    const submitted = await publicCaller.reviewerQueue.submit(sourceLead);
    expect(submitted).toEqual({ id: 42 });
    expect(queueDb.createReviewerQueueItem).toHaveBeenCalledWith(sourceLead);

    const ownerCaller = appRouter.createCaller(contextFor("admin"));
    await expect(ownerCaller.reviewerQueue.list({ status: "pending" })).resolves.toEqual([]);
    expect(queueDb.listReviewerQueueItems).toHaveBeenCalledWith("pending");

    await expect(ownerCaller.reviewerQueue.decide({ id: 42, status: "approved", reviewerNotes: "Confirmed a public first-party archive page." })).resolves.toEqual({ id: 42, status: "approved" });
    expect(queueDb.decideReviewerQueueItem).toHaveBeenCalledWith(
      { id: 42, status: "approved", reviewerNotes: "Confirmed a public first-party archive page." },
      31,
    );

    // A public submit must never trigger reviewer-only persistence paths.
    expect(queueDb.decideReviewerQueueItem).toHaveBeenCalledTimes(1);
    expect(queueDb.listReviewerQueueItems).toHaveBeenCalledTimes(1);
  });

  it("rejects non-http(s) URL schemes at the boundary", async () => {
    const publicCaller = appRouter.createCaller(contextFor(null));
    await expect(
      publicCaller.reviewerQueue.submit({ ...sourceLead, resourceUrl: "javascript:alert(1)" }),
    ).rejects.toThrow();
    expect(queueDb.createReviewerQueueItem).not.toHaveBeenCalled();
  });
});
