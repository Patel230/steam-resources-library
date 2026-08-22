import { z } from "zod";

export const reviewerQueueStatusSchema = z.enum(["pending", "researching", "approved", "rejected"]);

export const reviewerQueueSubmissionSchema = z.object({
  submitterName: z.string().trim().min(2, "Enter your name.").max(160),
  submitterEmail: z.string().trim().toLowerCase().email("Enter a valid email address.").max(320),
  country: z.string().trim().min(2, "Choose a country.").max(120),
  resourceUrl: z
    .string()
    .trim()
    .url("Enter a complete public URL.")
    .max(2048)
    .refine((value) => /^https?:\/\//i.test(value), "Only http(s) URLs are accepted."),
  resourceTitle: z.string().trim().min(2, "Name the source or archive.").max(255),
  sourceType: z.string().trim().min(2, "Choose a material type.").max(96),
  notes: z.string().trim().max(4000).optional().transform((value) => value || undefined),
});

export const reviewerQueueDecisionSchema = z
  .object({
    id: z.number().int().positive(),
    status: z.enum(["researching", "approved", "rejected"]),
    reviewerNotes: z.string().trim().max(4000).optional().transform((value) => value || undefined),
  })
  .superRefine((value, context) => {
    if ((value.status === "approved" || value.status === "rejected") && (value.reviewerNotes?.length ?? 0) < 5) {
      context.addIssue({ code: "custom", path: ["reviewerNotes"], message: "Record a concise decision note for approval or rejection." });
    }
  });

export type ReviewerQueueStatus = z.infer<typeof reviewerQueueStatusSchema>;
export type ReviewerQueueSubmission = z.infer<typeof reviewerQueueSubmissionSchema>;
export type ReviewerQueueDecision = z.infer<typeof reviewerQueueDecisionSchema>;
