/* STEAM Foundry legend: a clean, minimal navigation frame. */
import { Compass, MapPinned, Route, CircleCheck } from "lucide-react";
import { Link } from "wouter";

type AtlasLegendProps = {
  active: "field" | "archive" | "states";
};

const legendRoutes = [
  { id: "field", label: "Explore", href: "/" },
  { id: "archive", label: "Archive", href: "/#explore" },
  { id: "states", label: "Country ledger", href: "/coverage" },
] as const;

const subjects = ["GA", "EM", "DM", "CS", "S", "T", "E", "A"] as const;

export function AtlasLegend({ active }: AtlasLegendProps) {
  return (
    <aside className="atlas-legend" aria-label="STEAM Foundry navigation">
      <Link className="atlas-legend__brand" href="/">
        <Compass size={17} aria-hidden="true" />
        <span><strong>STEAM</strong> Foundry</span>
      </Link>

      <nav className="atlas-legend__routes" aria-label="Pages">
        {legendRoutes.map((route) => (
          <Link key={route.id} href={route.href} className={`atlas-legend__route ${active === route.id ? "is-active" : ""}`} aria-current={active === route.id ? "page" : undefined}>
            <span className="atlas-legend__route-dot" aria-hidden="true" />
            <span>{route.label}</span>
          </Link>
        ))}
      </nav>

      <div className="atlas-legend__subjects" aria-label="Subject tracks">
        {subjects.map((s) => <span key={s} className={`atlas-legend__subject atlas-legend__subject--${s.toLowerCase()}`}>{s}</span>)}
      </div>

      <div className="atlas-legend__meta">
        <span className="atlas-legend__meta-item"><CircleCheck size={13} aria-hidden="true" /> Verified &amp; free</span>
        <span className="atlas-legend__meta-item"><MapPinned size={13} aria-hidden="true" /> 193 states tracked</span>
      </div>
    </aside>
  );
}
