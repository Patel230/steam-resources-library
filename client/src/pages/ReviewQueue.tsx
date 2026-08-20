import { useMemo, useState } from "react";
import { ArrowLeft, CheckCircle2, ClipboardList, ExternalLink, Loader2, ShieldCheck, XCircle } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/_core/hooks/useAuth";
import { startLogin } from "@/const";
import { AtlasLegend } from "@/components/AtlasLegend";
import { trpc } from "@/lib/trpc";

type QueueFilter = "pending" | "researching" | "approved" | "rejected" | "all";
type DecisionStatus = Exclude<QueueFilter, "pending" | "all">;

const statusLabels: Record<Exclude<QueueFilter, "all">, string> = {
  pending: "Pending",
  researching: "Researching",
  approved: "Approved",
  rejected: "Rejected",
};

function formatDate(value: Date | string) {
  return new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function ReviewQueue() {
  const { user, loading, isAuthenticated } = useAuth();
  const [filter, setFilter] = useState<QueueFilter>("pending");
  const [notes, setNotes] = useState<Record<number, string>>({});
  const utils = trpc.useUtils();
  const isAdmin = user?.role === "admin";
  const queryInput = useMemo(() => filter === "all" ? undefined : { status: filter }, [filter]);
  const queue = trpc.reviewerQueue.list.useQuery(queryInput, { enabled: isAdmin });
  const decide = trpc.reviewerQueue.decide.useMutation({
    onSuccess: (_, variables) => {
      setNotes((current) => ({ ...current, [variables.id]: "" }));
      void utils.reviewerQueue.list.invalidate();
      toast.success(`Suggestion marked ${variables.status}`, { description: "The public catalog remains unchanged until a separate audited integration is completed." });
    },
    onError: (error) => toast.error("Review decision was not saved", { description: error.message }),
  });

  const decideItem = (id: number, status: DecisionStatus) => {
    const reviewerNotes = notes[id]?.trim();
    if ((status === "approved" || status === "rejected") && (reviewerNotes?.length ?? 0) < 5) {
      toast.error("Add a concise decision note", { description: "Approval and rejection require an auditable moderation note." });
      return;
    }
    decide.mutate({ id, status, reviewerNotes });
  };

  if (loading) return <main className="review-page review-page--loading"><Loader2 className="animate-spin" size={24} /> Loading reviewer access…</main>;

  if (!isAuthenticated) return <main className="review-page review-page--gate"><section><ShieldCheck size={32} /><p className="eyebrow">Signal Atlas / reviewer desk</p><h1>Sign in to open<br /><em>the review queue.</em></h1><p>Community contact details and moderation decisions are visible only to the archive owner.</p><button type="button" onClick={startLogin}>Sign in securely</button><a href="/">Return to the public archive <ArrowLeft size={15} /></a></section></main>;

  if (!isAdmin) return <main className="review-page review-page--gate"><section><ShieldCheck size={32} /><p className="eyebrow">Signal Atlas / access boundary</p><h1>This desk is<br /><em>owner-restricted.</em></h1><p>The public archive remains available, but submitted source leads and reviewer notes are private.</p><a href="/">Return to the public archive <ArrowLeft size={15} /></a></section></main>;

  return <div className="review-page">
    <header className="review-page__header"><a className="brand-lockup" href="/" aria-label="Signal Atlas home"><img src="/manus-storage/signal-atlas-mark_db2cb221.png" alt="" className="brand-mark" /><span><strong>Signal</strong> Atlas</span></a><nav aria-label="Review navigation"><a href="/">Public archive</a><a href="/coverage">Coverage ledger</a></nav><span><ShieldCheck size={15} /> Owner review desk</span></header>
    <AtlasLegend active="field" />
    <main className="review-page__main">
      <section className="review-page__hero"><div><p className="eyebrow eyebrow--light"><span className="eyebrow-marker coordinate-marker" /> Private moderation surface</p><h1>Review source leads<br /><em>before they become signals.</em></h1><p>Approving a lead records an editorial decision only. It never publishes a resource; catalog promotion still requires the separate first-party, free-access, and item-level verification workflow.</p></div><div className="review-page__rule"><ClipboardList size={20} /><strong>Review rule</strong><span>Validate provenance · public access · GA/EM/DM relevance · reproducible item links</span></div></section>
      <section className="review-page__workbench" aria-label="Reviewer queue">
        <div className="review-page__toolbar"><div><p className="eyebrow">Queue status</p><h2>{queue.data?.length ?? 0} {filter === "all" ? "recorded leads" : statusLabels[filter].toLowerCase() + " leads"}</h2></div><div className="review-page__filters" role="group" aria-label="Filter suggestions by status">{(["pending", "researching", "approved", "rejected", "all"] as QueueFilter[]).map((status) => <button key={status} type="button" className={filter === status ? "is-active" : ""} onClick={() => setFilter(status)}>{status === "all" ? "All" : statusLabels[status]}</button>)}</div></div>
        {queue.isLoading && <div className="review-page__empty"><Loader2 className="animate-spin" size={20} /> Loading the queue…</div>}
        {queue.isError && <div className="review-page__empty"><XCircle size={20} /><h3>The queue could not be loaded.</h3><p>{queue.error.message}</p></div>}
        {!queue.isLoading && !queue.isError && queue.data?.length === 0 && <div className="review-page__empty"><ClipboardList size={24} /><h3>No {filter === "all" ? "source leads" : statusLabels[filter].toLowerCase() + " leads"} right now.</h3><p>New community suggestions will appear here for independent review.</p></div>}
        <div className="review-page__list">{queue.data?.map((item) => <article className="review-card" key={item.id}>
          <div className="review-card__meta"><span className={`review-status review-status--${item.status}`}>{statusLabels[item.status]}</span><span>#{item.id} · submitted {formatDate(item.submittedAt)}</span></div>
          <div className="review-card__body"><div><p className="eyebrow">{item.country} / {item.sourceType}</p><h3>{item.resourceTitle}</h3><a href={item.resourceUrl} target="_blank" rel="noreferrer">Open submitted URL <ExternalLink size={14} /></a></div><dl><div><dt>Submitter</dt><dd>{item.submitterName}</dd></div><div><dt>Contact</dt><dd><a href={`mailto:${item.submitterEmail}`}>{item.submitterEmail}</a></dd></div>{item.notes && <div className="review-card__notes"><dt>Evidence notes</dt><dd>{item.notes}</dd></div>}</dl></div>
          {item.status === "pending" || item.status === "researching" ? <div className="review-card__decision"><label htmlFor={`notes-${item.id}`}>Reviewer note <textarea id={`notes-${item.id}`} value={notes[item.id] ?? ""} onChange={(event) => setNotes((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Record access evidence, provenance checks, or a decision reason." rows={3} /></label><div><button type="button" onClick={() => decideItem(item.id, "researching")} disabled={decide.isPending}><ClipboardList size={15} /> Mark researching</button><button type="button" className="review-card__approve" onClick={() => decideItem(item.id, "approved")} disabled={decide.isPending}><CheckCircle2 size={15} /> Approve lead</button><button type="button" className="review-card__reject" onClick={() => decideItem(item.id, "rejected")} disabled={decide.isPending}><XCircle size={15} /> Reject lead</button></div></div> : <div className="review-card__completed"><strong>{statusLabels[item.status]} {item.reviewedAt ? formatDate(item.reviewedAt) : ""}</strong><p>{item.reviewerNotes || "No reviewer note recorded."}</p></div>}
        </article>)}</div>
      </section>
    </main>
  </div>;
}
