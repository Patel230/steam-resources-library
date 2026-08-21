/* Signal Atlas reminder: cards should feel like annotated index cards, with provenance before decoration. */
/* Signal Atlas card language: mineral-paper surfaces, coordinate markers, and visible provenance before decoration. */
import { ArrowUpRight, BadgeCheck, BookOpen, Globe2, Languages, Sparkles, TriangleAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CatalogRow, accessLabel, displayNotes, displaySourceTitle, displayTitle, hasAccessCaveat, hostFromUrl, isFreeResource, lastVerifiedDate, resourceKind, rowTracks, sourceQuality, trackDefinitions, verificationLabel } from "@/lib/catalog";

type ResourceCardProps = {
  row: CatalogRow;
  onInspect: (row: CatalogRow) => void;
  index: number;
};

export function ResourceCard({ row, onInspect, index }: ResourceCardProps) {
  const tracks = rowTracks(row);
  const primaryTrack = tracks[0] ?? "GA";
  const meta = trackDefinitions[primaryTrack];
  const isGateway = row.resource_class === "Official gateway";
  const isFree = isFreeResource(row);
  const hasCaveat = hasAccessCaveat(row);

  return (
    <article className={`resource-card resource-card--${primaryTrack.toLowerCase()} ${isFree ? "resource-card--free" : ""} ${hasCaveat ? "resource-card--caveat" : ""}`} style={{ "--stagger": `${Math.min(index, 8) * 35}ms` } as React.CSSProperties}>
      <div className={`resource-card__ribbon resource-card__ribbon--${primaryTrack.toLowerCase()}`}><span />{row.priority === "A" ? "Verified first-party" : "Catalog source"}</div>
      <div className="resource-card__topline">
        <div className="resource-card__tags">
          {tracks.map((track) => (
            <span key={track} className={`track-chip track-chip--${track.toLowerCase()}`}>
              {track}
            </span>
          ))}
          {isGateway && <span className="official-pill"><BadgeCheck size={13} /> Official gateway</span>}
          {isFree && <span className="free-pill"><BadgeCheck size={13} /> Free access</span>}
          {hasCaveat && <span className="caveat-pill" title={verificationLabel(row)}><TriangleAlert size={13} /> Access caveat</span>}
        </div>
        <span className="resource-card__kind"><small>Material</small>{resourceKind(row)}</span>
      </div>

      <div className="resource-card__body">
        <p className="resource-card__route"><span className={`resource-card__subject-mark resource-card__subject-mark--${primaryTrack.toLowerCase()}`} title={meta.label}>{primaryTrack}</span><span className="coordinate-marker" /> Route {String(index + 1).padStart(3, "0")} · {row.country}</p>
        <h3>{displayTitle(row)}</h3>
        <p className="resource-card__source"><BookOpen size={14} /><span className="resource-card__source-label">Source</span> {displaySourceTitle(row)}</p>
        <p className="resource-card__trustline"><BadgeCheck size={13} /><strong>{sourceQuality(row)}</strong><span>·</span><span>{verificationLabel(row)}</span></p>
        <p className="resource-card__notes">{displayNotes(row) || `${meta.label} resource from ${hostFromUrl(row.resource_url)}.`}</p>
      </div>

      <div className="resource-card__footer">
        <div className="resource-card__micro-meta">
          <span><Globe2 size={13} /> {hostFromUrl(row.resource_url)}</span>
          <span><Languages size={13} /> {row.language || "English"}</span>
          {isFree && <span className={`access-meta ${hasCaveat ? "access-meta--warning" : ""}`}><BadgeCheck size={13} /> {hasCaveat ? "Check access" : accessLabel(row)}</span>}
          {!isFree && <span className="access-meta access-meta--muted">{verificationLabel(row)}</span>}
          <span className="trust-meta"><span className="coordinate-marker" /> {sourceQuality(row)} · verified {lastVerifiedDate(row)}</span>
        </div>
        <div className="resource-card__actions">
          <Button variant="ghost" size="sm" className="inspect-button" onClick={() => onInspect(row)}>
            Inspect <Sparkles size={14} />
          </Button>
          <a className="open-link" href={row.resource_url} target="_blank" rel="noreferrer">
            Open <ArrowUpRight size={15} />
          </a>
        </div>
      </div>
    </article>
  );
}
