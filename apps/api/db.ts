import { and, desc, eq, inArray, sql } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, reviewerQueue, users } from "../../drizzle/schema";
import { ENV } from './_core/env';
import type { ReviewerQueueDecision, ReviewerQueueStatus, ReviewerQueueSubmission } from "./reviewerQueue";

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    throw new Error("[Database] Cannot upsert user: database not available");
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

/** Invalidates all previously issued session JWTs for the user. */
export async function bumpUserTokenVersion(openId: string): Promise<void> {
  const db = requireDatabase(await getDb());
  await db
    .update(users)
    .set({ tokenVersion: sql`${users.tokenVersion} + 1` })
    .where(eq(users.openId, openId));
}

function requireDatabase<T>(database: T | null): T {
  if (!database) throw new Error("The reviewer queue is temporarily unavailable. Please try again shortly.");
  return database;
}

export async function createReviewerQueueItem(input: ReviewerQueueSubmission) {
  const db = requireDatabase(await getDb());
  const result = await db.insert(reviewerQueue).values({
    ...input,
    notes: input.notes ?? null,
  }).$returningId();

  const id = result[0]?.id;
  if (!id) throw new Error("The suggestion could not be recorded.");
  return id;
}

export async function listReviewerQueueItems(status?: ReviewerQueueStatus) {
  const db = requireDatabase(await getDb());
  return db
    .select()
    .from(reviewerQueue)
    .where(status ? eq(reviewerQueue.status, status) : undefined)
    .orderBy(desc(reviewerQueue.submittedAt));
}

export async function decideReviewerQueueItem(input: ReviewerQueueDecision, reviewerId: number) {
  const db = requireDatabase(await getDb());
  // Only pending/researching items may transition; this makes the decision a
  // compare-and-set so concurrent reviewers cannot silently overwrite each
  // other's verdict on an already-decided item.
  const result = await db
    .update(reviewerQueue)
    .set({
      status: input.status,
      reviewerId,
      reviewerNotes: input.reviewerNotes ?? null,
      reviewedAt: new Date(),
    })
    .where(
      and(
        eq(reviewerQueue.id, input.id),
        inArray(reviewerQueue.status, ["pending", "researching"]),
      ),
    );

  if ((result[0]?.affectedRows ?? 0) === 0) {
    throw new Error("The suggestion no longer exists or was already decided.");
  }
  return { id: input.id, status: input.status } as const;
}
