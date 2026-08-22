import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import { reviewerQueueDecisionSchema, reviewerQueueSubmissionSchema } from "./reviewerQueue";
import type { TrpcContext } from "./_core/context";

function contextFor(role: "admin" | "user"): TrpcContext {
  return {
    user: {
      id: 19,
      openId: "reviewer-test-user",
      name: "Reviewer Test",
      email: "reviewer@example.com",
      loginMethod: "manus",
      role,
      tokenVersion: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
    req: {} as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

describe("reviewer queue contracts", () => {
  it("accepts a complete public-source lead and rejects incomplete URLs", () => {
    const valid = reviewerQueueSubmissionSchema.parse({
      submitterName: "Archive contributor",
      submitterEmail: "contributor@example.com",
      country: "Bangladesh",
      resourceUrl: "https://example.edu/math/archive",
      resourceTitle: "Example University mathematics archive",
      sourceType: "University examination papers",
      notes: "Direct public archive page.",
    });

    expect(valid.submitterEmail).toBe("contributor@example.com");
    expect(() => reviewerQueueSubmissionSchema.parse({ ...valid, resourceUrl: "not-a-url" })).toThrow();
  });

  it("permits only explicit moderator outcomes", () => {
    expect(reviewerQueueDecisionSchema.parse({ id: 7, status: "researching", reviewerNotes: "Checking source ownership." }).status).toBe("researching");
    expect(() => reviewerQueueDecisionSchema.parse({ id: 7, status: "pending" })).toThrow();
  });

  it("does not disclose the queue to a non-admin user", async () => {
    const caller = appRouter.createCaller(contextFor("user"));
    await expect(caller.reviewerQueue.list()).rejects.toMatchObject({ code: "FORBIDDEN" });
  });
});
