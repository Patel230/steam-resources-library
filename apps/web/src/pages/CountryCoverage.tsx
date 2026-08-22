/* STEAM Foundry coverage directory: an atlas ledger for every UN member state, with pending scope kept visible. */
/* STEAM Foundry country ledger: map-like scanning, quiet mineral surfaces, and clear saffron progress cues make research gaps legible without overstating coverage. */
import { useEffect, useMemo, useState } from "react";
import { ArrowRight, ArrowUpRight, Check, Compass, MapPinned, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AtlasLegend } from "@/components/AtlasLegend";
import { MEMBER_STATE_SOURCE } from "@/data/memberStates";
import { regionForState } from "@/data/regions";
import { CoverageStatus, coverageIndex, globalTrackStats, regionCoverage } from "@/lib/coverage";

type StatusFilter = "all" | CoverageStatus;
type ProgressFilter = "all" | "near";
type ProgressOrder = "ledger" | "closest" | "progress" | "gap" | "alpha";

const progressOrders: Array<{ value: ProgressOrder; label: string; resultCopy: string }> = [
  { value: "ledger", label: "Ledger order", resultCopy: "canonical 193-state ledger order" },
  { value: "closest", label: "Closest below 100", resultCopy: "closest active routes below the 100-resource target" },
  { value: "progress", label: "Most resources", resultCopy: "most verified free resources first" },
  { value: "gap", label: "Largest gap", resultCopy: "largest remaining gap first" },
  { value: "alpha", label: "A–Z", resultCopy: "alphabetical country order" },
];

const statusCopy: Record<CoverageStatus, { label: string; short: string }> = {
  active: { label: "Active", short: "Free resources" },
  caveat: { label: "Active with caveat", short: "Free resources · access caveat" },
  pending: { label: "Pending", short: "Free tranche pending" },
};

const prettyCount = (value: number) => new Intl.NumberFormat("en-US").format(value);
const isNearTarget = (entry: { freeCount: number }) => entry.freeCount > 0 && entry.freeCount < 100;

export default function CountryCoverage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [progress, setProgress] = useState<ProgressFilter>(() => new URLSearchParams(window.location.search).get("progress") === "near" ? "near" : "all");
  const [order, setOrder] = useState<ProgressOrder>(() => {
    const value = new URLSearchParams(window.location.search).get("order");
    return progressOrders.some((option) => option.value === value) ? value as ProgressOrder : "ledger";
  });

  const counts = useMemo(() => ({
    active: coverageIndex.filter((entry) => entry.status === "active").length,
    caveat: coverageIndex.filter((entry) => entry.status === "caveat").length,
    pending: coverageIndex.filter((entry) => entry.status === "pending").length,
    near: coverageIndex.filter((entry) => isNearTarget(entry)).length,
  }), []);

  const activeOrder = progress === "near" && order === "ledger" ? "closest" : order;
  const activeOrderCopy = progressOrders.find((option) => option.value === activeOrder)?.resultCopy ?? "canonical 193-state ledger order";
  const nearestTargetFive = useMemo(() => coverageIndex
    .filter((entry) => isNearTarget(entry))
    .sort((left, right) => right.freeCount - left.freeCount || left.state.localeCompare(right.state))
    .slice(0, 5), []);

  const visibleEntries = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const matchingEntries = coverageIndex.filter((entry) => {
      const matchesStatus = status === "all" || entry.status === status;
      const matchesProgress = progress === "all" || isNearTarget(entry);
      const matchesQuery = !normalizedQuery || entry.state.toLowerCase().includes(normalizedQuery);
      return matchesStatus && matchesProgress && matchesQuery;
    });
    return matchingEntries.sort((left, right) => {
      if (activeOrder === "alpha") return left.state.localeCompare(right.state);
      if (activeOrder === "progress") return right.freeCount - left.freeCount || left.state.localeCompare(right.state);
      if (activeOrder === "gap") return (100 - Math.min(left.freeCount, 100)) - (100 - Math.min(right.freeCount, 100)) || left.state.localeCompare(right.state);
      if (activeOrder === "closest") {
        const leftBelowTarget = isNearTarget(left);
        const rightBelowTarget = isNearTarget(right);
        if (leftBelowTarget !== rightBelowTarget) return leftBelowTarget ? -1 : 1;
        return right.freeCount - left.freeCount || left.state.localeCompare(right.state);
      }
      return 0;
    });
  }, [activeOrder, progress, query, status]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (progress === "near") params.set("progress", "near");
    if (order !== "ledger") params.set("order", order);
    const queryString = params.toString();
    window.history.replaceState(null, "", `${window.location.pathname}${queryString ? `?${queryString}` : ""}`);
  }, [order, progress]);

  const clearDirectoryFilters = () => {
    setQuery("");
    setStatus("all");
    setProgress("all");
    setOrder("ledger");
  };

  return (
    <div className="coverage-page">
      <AtlasLegend active="states" />
      <header className="coverage-page__header">
        <a className="brand-lockup" href="/" aria-label="STEAM Foundry home">
          <img src="steam-foundry-mark.svg" alt="" className="brand-mark" />
          <span><strong>STEAM</strong> Foundry</span>
        </a>
        <nav className="coverage-page__nav" aria-label="Coverage navigation">
          <a href="/">Explore archive</a>
          <a href="/coverage" aria-current="page">Country directory</a>
        </nav>
        <span className="coverage-page__header-note"><span /> 193 member-state ledger</span>
      </header>

      <main>
        <section className="coverage-page__hero">
          <div className="coverage-page__hero-inner">
            <div>
              <p className="eyebrow eyebrow--light"><span className="eyebrow-marker coordinate-marker" /> Coverage directory / 193 states</p>
              <h1>Know what is mapped.<br /><em>See what is next.</em></h1>
              <p className="coverage-page__hero-copy">The country ledger separates live free-resource coverage from pending expansion. The threshold route ranks every country with verified free records that remains below 100, making the next honest research candidates visible.</p>
              <div className="coverage-page__hero-actions">
                <Button asChild className="coverage-page__primary-action"><a href="/">Browse the archive <ArrowRight size={16} /></a></Button>
                <a className="coverage-page__source-link" href="/coverage?progress=near">Nearest to 100 <ArrowRight size={15} /></a>
                <a className="coverage-page__source-link" href={MEMBER_STATE_SOURCE} target="_blank" rel="noreferrer">UN roster source <ArrowUpRight size={15} /></a>
              </div>
            </div>
            <div className="coverage-page__hero-note" aria-label="Coverage status summary">
              <div className="coverage-page__hero-note-top"><MapPinned size={17} /><span>Field note / 193</span></div>
              <strong>{prettyCount(counts.active + counts.caveat)} active</strong>
              <span>member-state tracks with free-tranche records</span>
              <div className="coverage-page__hero-route"><i /><i /><i /><i /><i /></div>
              <small>{prettyCount(counts.pending)} pending states remain visible for the next research pass.</small>
            </div>
          </div>
        </section>

        <section className="coverage-page__body">
          <div className="coverage-page__stats" aria-label="Coverage statistics">
            <div><span>Active</span><strong>{prettyCount(counts.active)}</strong><small>verified free tranche</small></div>
            <div><span>Active with caveat</span><strong>{prettyCount(counts.caveat)}</strong><small>access needs checking</small></div>
            <div><span>Pending</span><strong>{prettyCount(counts.pending)}</strong><small>no free record yet</small></div>
            <div><span>Global track</span><strong>{prettyCount(globalTrackStats.freeCount)}</strong><small>{prettyCount(globalTrackStats.catalogCount)} catalog records</small></div>
          </div>

          <nav className="coverage-route-key" aria-label="Atlas coverage route key">
            <div className="coverage-route-key__compass"><Compass size={17} /><span>North / coverage field</span><small>SA · 193</small></div>
            <a href="/" className="coverage-route-key__route"><b>01</b><span>Archive</span><small>Source trails</small></a>
            <a href="/coverage" className="coverage-route-key__route is-active" aria-current="page"><b>02</b><span>Directory</span><small>Country ledger</small></a>
            <a href="#coverage-ledger" className="coverage-route-key__route"><b>03</b><span>Threshold</span><small>100-resource route</small></a>
            <a href="/?country=Bangladesh#explore" className="coverage-route-key__route"><b>04</b><span>Source desk</span><small>Public access review</small></a>
          </nav>

          <div className="coverage-directory__heading" id="coverage-ledger">
            <div><p className="eyebrow"><span className="eyebrow-marker coordinate-marker" /> The country ledger</p><h2>Every state gets a line.</h2></div>
            <p>Search the canonical member-state roster, filter by status, or surface the states nearest to the 100-resource target. Counts are derived from the verified catalog index.</p>
          </div>

          <section className="coverage-priority-brief" aria-labelledby="coverage-priority-title">
            <div className="coverage-priority-brief__heading"><p className="eyebrow"><span className="eyebrow-marker coordinate-marker" /> Research priority / 05</p><h3 id="coverage-priority-title">The next five country routes.</h3><p>These active tracks have verified free materials and are closest to the 100-resource milestone. Their visual meters show the remaining research gap.</p></div>
            <div className="coverage-priority-brief__grid">
              {nearestTargetFive.map((entry, index) => {
                const progressValue = Math.min(entry.freeCount, 100);
                const remaining = Math.max(100 - entry.freeCount, 0);
                return <a className="coverage-priority-brief__card" href={`/?country=${encodeURIComponent(entry.state)}#explore`} key={entry.state}>
                  <span className="coverage-priority-brief__rank">0{index + 1}</span>
                  <span className="coverage-priority-brief__state">{entry.state}</span>
                  <span className="coverage-priority-brief__metric"><b>{prettyCount(entry.freeCount)}</b> verified free</span>
                  <span className="coverage-priority-brief__meter" aria-label={`${entry.state}: ${progressValue}% of the 100-resource target`}><i style={{ width: `${progressValue}%` }} /></span>
                  <span className="coverage-priority-brief__gap">{progressValue}% mapped <b>{prettyCount(remaining)} to target</b><ArrowRight size={13} /></span>
                </a>;
              })}
            </div>
          </section>

          <section className="regional-summary" aria-labelledby="regional-summary-title">
            <div className="regional-summary__heading"><p className="eyebrow"><span className="eyebrow-marker coordinate-marker" /> Regional signal</p><h3 id="regional-summary-title">See the field by region.</h3><p>Regional totals are rollups of the same 193-state ledger. Select a region to open the archive pre-filtered to that route.</p></div>
            <div className="regional-summary__grid">
              {regionCoverage.map((summary) => <a className="regional-summary__card" key={summary.region} href={`/?region=${encodeURIComponent(summary.region)}#explore`}>
                <span className="regional-summary__kicker">{summary.total} states</span>
                <strong>{summary.region}</strong>
                <span className="regional-summary__meta"><b>{prettyCount(summary.freeCount)}</b> free · <b>{summary.active + summary.caveat}</b> active</span>
                <span className="regional-summary__meta">{summary.pending} pending · {summary.catalogCount} catalog</span>
                <span className="regional-summary__link">Open regional route <ArrowRight size={13} /></span>
              </a>)}
            </div>
          </section>

          <div className="coverage-directory__toolbar">
            <div className="coverage-directory__search"><Search size={16} /><Input aria-label="Search member states" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search a member state" />{query && <button aria-label="Clear country search" onClick={() => setQuery("")}><X size={14} /></button>}</div>
            <div className="coverage-directory__filters" aria-label="Filter country status">
              {(["all", "active", "caveat", "pending"] as StatusFilter[]).map((value) => <button key={value} type="button" aria-pressed={status === value} className={status === value ? "is-active" : ""} onClick={() => setStatus(value)}>{value === "all" ? "All states" : statusCopy[value].label}</button>)}
            </div>
            <div className="coverage-directory__progress-filter" aria-label="Filter progress toward the 100-resource target"><span>100-resource route</span><button type="button" aria-pressed={progress === "near"} className={progress === "near" ? "is-active" : ""} onClick={() => { const next = progress === "near" ? "all" : "near"; setProgress(next); if (next === "near" && order === "ledger") setOrder("closest"); }}>Nearest below 100 <b>{counts.near}</b></button></div>
            <label className="coverage-directory__sort"><span>Rank by</span><select value={order} onChange={(event) => setOrder(event.target.value as ProgressOrder)} aria-label="Sort countries by target progress">{progressOrders.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
            {(query || status !== "all" || progress !== "all" || order !== "ledger") && <button className="coverage-directory__reset" onClick={clearDirectoryFilters}>Reset <X size={13} /></button>}
          </div>

          <div className="coverage-directory__result-meta"><span><strong>{prettyCount(visibleEntries.length)}</strong> of 193 member states shown · {activeOrderCopy}</span><span><i className="coverage-status-dot coverage-status-dot--active" /> Active <i className="coverage-status-dot coverage-status-dot--caveat" /> Caveat <i className="coverage-status-dot coverage-status-dot--pending" /> Pending</span></div>

          {visibleEntries.length > 0 ? <div className="coverage-directory__grid" role="list" aria-label="UN member-state coverage entries">
            {visibleEntries.map((entry, index) => <article className={`coverage-entry coverage-entry--${entry.status}`} role="listitem" key={entry.state}>
              <span className="coverage-entry__index">{String(index + 1).padStart(3, "0")}</span>
              <div className="coverage-entry__body"><h3>{entry.state}</h3><p><span className="coverage-entry__region"><i className="coverage-entry__region-marker" />{regionForState(entry.state)}</span> · {entry.freeCount > 0 ? `${prettyCount(entry.freeCount)} free · ${prettyCount(entry.catalogCount)} catalog` : "No free-tranche record yet"}</p><div className="coverage-entry__progress" aria-label={`${entry.state}: ${Math.min(entry.freeCount, 100)} of 100 verified free resources`}><span className="coverage-entry__progress-track"><i style={{ width: `${Math.min(100, entry.freeCount)}%` }} /></span><small>{entry.freeCount >= 100 ? "100+ / target met" : `${entry.freeCount}% · ${100 - Math.min(entry.freeCount, 100)} remaining`}</small></div><a className="coverage-entry__open" href={`/?country=${encodeURIComponent(entry.state)}#explore`}>Open country route <ArrowRight size={12} /></a></div>
              <span className="coverage-entry__status"><i className={`coverage-status-dot coverage-status-dot--${entry.status}`} />{statusCopy[entry.status].label}</span>
            </article>)}
          </div> : <div className="coverage-directory__empty"><MapPinned size={22} /><h3>No state matches that route.</h3><p>Clear the search or return to the full 193-state ledger.</p><Button variant="outline" onClick={clearDirectoryFilters}>Reset directory</Button></div>}
        </section>
      </main>

      <footer className="coverage-page__footer"><a className="brand-lockup" href="/"><img src="steam-foundry-mark.svg" alt="" className="brand-mark" /><span><strong>STEAM</strong> Foundry</span></a><span>Country coverage is a live research ledger, not a completeness claim.</span><a href="/">Return to explore <ArrowRight size={14} /></a></footer>
    </div>
  );
}
