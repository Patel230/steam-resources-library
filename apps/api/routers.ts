import { COOKIE_NAME } from "@shared/const";
import * as db from "./db";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { adminProcedure, publicProcedure, router } from "./_core/trpc";
import { reviewerQueueDecisionSchema, reviewerQueueStatusSchema, reviewerQueueSubmissionSchema } from "./reviewerQueue";
import { z } from "zod";

export const appRouter = router({
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),
  reviewerQueue: router({
    /** Public leads are stored for manual review only; this never edits catalog files. */
    submit: publicProcedure.input(reviewerQueueSubmissionSchema).mutation(async ({ input }) => {
      const id = await db.createReviewerQueueItem(input);
      return { id } as const;
    }),
    list: adminProcedure
      .input(z.object({ status: reviewerQueueStatusSchema.optional() }).optional())
      .query(({ input }) => db.listReviewerQueueItems(input?.status)),
    decide: adminProcedure.input(reviewerQueueDecisionSchema).mutation(({ ctx, input }) => {
      return db.decideReviewerQueueItem(input, ctx.user.id);
    }),
  }),
});

export type AppRouter = typeof appRouter;
