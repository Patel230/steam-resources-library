/* Signal Atlas source desk: capture public-access leads for independent, non-automatic review. */
import { useId, useState } from "react";
import { Check, ClipboardCheck, Link2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";

type Suggestion = {
  submitterName: string;
  submitterEmail: string;
  resourceTitle: string;
  resourceUrl: string;
  sourceType: string;
  notes: string;
};

const initialSuggestion: Suggestion = { submitterName: "", submitterEmail: "", resourceTitle: "", resourceUrl: "", sourceType: "Past papers / problems", notes: "" };

type BangladeshSourceFormProps = { country?: string };

export function BangladeshSourceForm({ country = "Bangladesh" }: BangladeshSourceFormProps) {
  const [suggestion, setSuggestion] = useState<Suggestion>(initialSuggestion);
  const [queued, setQueued] = useState(false);
  const baseId = useId();
  const isBangladesh = country === "Bangladesh";
  const update = <K extends keyof Suggestion>(key: K, value: Suggestion[K]) => setSuggestion((current) => ({ ...current, [key]: value }));
  const submitSuggestion = trpc.reviewerQueue.submit.useMutation({
    onSuccess: () => {
      setSuggestion(initialSuggestion);
      setQueued(true);
      toast.success("Source suggestion recorded", { description: "It is now awaiting independent access and provenance review." });
    },
    onError: (error) => toast.error("The suggestion could not be recorded", { description: error.message }),
  });

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setQueued(false);
    submitSuggestion.mutate({ ...suggestion, country });
  };

  return <section className="bangladesh-source-desk" aria-labelledby={`${baseId}-title`}>
    <div className="bangladesh-source-desk__intro">
      <p className="eyebrow"><span className="eyebrow-marker coordinate-marker" /> {country} / source desk</p>
      <h2 id={`${baseId}-title`}>Point us to a source<br /><em>we can verify.</em></h2>
      <p>{isBangladesh ? "The current Bangladesh organiser collection is not indexed as reproducible item-level public links, so it remains deliberately outside automatic expansion." : `Know a public ${country} organiser, university, or official exam route that should be considered? Send a concise evidence lead for independent review.`}</p>
      <div className="bangladesh-source-desk__criteria"><span><Check size={14} /> Direct public access</span><span><Check size={14} /> Organiser or institutional provenance</span><span><Check size={14} /> GA, EM, or DM relevance</span></div>
      <small>Submissions enter a private reviewer queue. They are never published automatically and must pass an independent first-party and public-access check before any catalog change.</small>
    </div>

    <form className="bangladesh-source-desk__form" onSubmit={submit}>
      <label htmlFor={`${baseId}-person`}>Your name<input id={`${baseId}-person`} required minLength={2} value={suggestion.submitterName} onChange={(event) => update("submitterName", event.target.value)} placeholder="Your name" /></label>
      <label htmlFor={`${baseId}-email`}>Your email<input id={`${baseId}-email`} required type="email" value={suggestion.submitterEmail} onChange={(event) => update("submitterEmail", event.target.value)} placeholder="you@example.com" /></label>
      <label htmlFor={`${baseId}-title`}>Source or archive title<input id={`${baseId}-title`} required minLength={2} value={suggestion.resourceTitle} onChange={(event) => update("resourceTitle", event.target.value)} placeholder="Example: University mathematics past papers" /></label>
      <label htmlFor={`${baseId}-url`}>Public source URL<input id={`${baseId}-url`} required type="url" value={suggestion.resourceUrl} onChange={(event) => update("resourceUrl", event.target.value)} placeholder="https://…" /></label>
      <label htmlFor={`${baseId}-material`}>Material type<select id={`${baseId}-material`} value={suggestion.sourceType} onChange={(event) => update("sourceType", event.target.value)}><option>Past papers / problems</option><option>Official solutions</option><option>Olympiad / contest archive</option><option>University examination papers</option><option>MCQs / assignments / quizzes</option></select></label>
      <label htmlFor={`${baseId}-notes`}>Why is this source reproducibly public?<textarea id={`${baseId}-notes`} value={suggestion.notes} onChange={(event) => update("notes", event.target.value)} placeholder="Note the archive page, direct-download pattern, public-access evidence, and relevant years." rows={4} /></label>
      <button type="submit" className="bangladesh-source-desk__submit" disabled={submitSuggestion.isPending}>{submitSuggestion.isPending ? <Loader2 className="animate-spin" size={16} /> : <ClipboardCheck size={16} />}{submitSuggestion.isPending ? "Recording source" : "Send for review"}</button>
    </form>

    {queued && <div className="bangladesh-source-desk__packet" aria-live="polite"><div><p className="eyebrow eyebrow--muted">Reviewer queue</p><strong>Recorded for independent review</strong></div><p><Link2 size={14} /> Your lead is stored privately for the Atlas reviewer. It will not change the public catalog unless direct public access, provenance, relevance, and a fresh URL check are confirmed.</p></div>}
  </section>;
}
