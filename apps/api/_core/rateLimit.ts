import type { Request } from "express";

type Bucket = { count: number; resetAt: number };

const buckets = new Map<string, Bucket>();

function clientIp(req: Request): string {
  const forwarded = req.headers?.["x-forwarded-for"];
  if (typeof forwarded === "string" && forwarded.length > 0) {
    return forwarded.split(",")[0]?.trim() || "unknown";
  }
  return req.ip ?? req.socket?.remoteAddress ?? "unknown";
}

/**
 * Fixed-window in-memory rate limiter for tRPC procedures. Best-effort
 * abuse protection: sufficient for a single instance behind the gateway.
 */
export function rateLimit(
  req: Request,
  options: { key: string; limit: number; windowMs: number }
): void {
  const now = Date.now();
  const id = `${options.key}:${clientIp(req)}`;
  const bucket = buckets.get(id);

  if (!bucket || bucket.resetAt <= now) {
    buckets.set(id, { count: 1, resetAt: now + options.windowMs });
    return;
  }

  bucket.count += 1;
  if (bucket.count > options.limit) {
    const retryAfterSec = Math.ceil((bucket.resetAt - now) / 1000);
    throw new Error(`Too many requests. Please try again in ${retryAfterSec}s.`);
  }

  // Opportunistic cleanup so the map cannot grow unbounded.
  if (buckets.size > 10_000) {
    for (const [key, value] of buckets) {
      if (value.resetAt <= now) buckets.delete(key);
    }
  }
}
