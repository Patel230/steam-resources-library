import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Community leads are intentionally separated from catalog records. A reviewer
 * must independently verify provenance and public access before manually adding
 * any resource to the static, audited catalog.
 */
export const reviewerQueue = mysqlTable("reviewer_queue", {
  id: int("id").autoincrement().primaryKey(),
  submitterName: varchar("submitterName", { length: 160 }).notNull(),
  submitterEmail: varchar("submitterEmail", { length: 320 }).notNull(),
  country: varchar("country", { length: 120 }).notNull(),
  resourceUrl: varchar("resourceUrl", { length: 2048 }).notNull(),
  resourceTitle: varchar("resourceTitle", { length: 255 }).notNull(),
  sourceType: varchar("sourceType", { length: 96 }).notNull(),
  notes: text("notes"),
  status: mysqlEnum("status", ["pending", "researching", "approved", "rejected"]).default("pending").notNull(),
  submittedAt: timestamp("submittedAt").defaultNow().notNull(),
  reviewedAt: timestamp("reviewedAt"),
  reviewerId: int("reviewerId").references(() => users.id, { onDelete: "set null" }),
  reviewerNotes: text("reviewerNotes"),
});

export type ReviewerQueueItem = typeof reviewerQueue.$inferSelect;
export type InsertReviewerQueueItem = typeof reviewerQueue.$inferInsert;
