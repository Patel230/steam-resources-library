/* STEAM Foundry legend: a persistent cartographic frame with numbered routes, subject markers, and one decisive saffron active state. */
import { Compass, MapPinned, Route } from "lucide-react";

type AtlasLegendProps = {
  active: "field" | "archive" | "states";
};

const legendRoutes = [
  { id: "field", number: "01", label: "Field note", href: "/", marker: "N" },
  { id: "archive", number: "02", label: "Archive", href: "/#explore", marker: "GA / EM / DM" },
  { id: "states", number: "03", label: "State ledger", href: "/coverage", marker: "193" },
] as const;

export function AtlasLegend({ active }: AtlasLegendProps) {
  const activeRoute = legendRoutes.find((route) => route.id === active);

  return (
    <aside className="atlas-legend" aria-label="STEAM Foundry navigation legend">
      <div className="atlas-legend__cap"><Compass size={16} aria-hidden="true" /><span>STEAM Foundry</span><b>SF / 193</b></div>
      <div className="atlas-legend__north"><i aria-hidden="true" /><span>N / 014</span><small>W 073 · E 118</small></div>
      <p className="atlas-legend__location"><span>Current coordinate</span><strong>{activeRoute?.number} / {activeRoute?.label}</strong></p>
      <nav className="atlas-legend__routes" aria-label="Atlas routes">
        {legendRoutes.map((route) => <a key={route.id} href={route.href} className={active === route.id ? "is-active" : ""} aria-current={active === route.id ? "page" : undefined}>
          <span className="atlas-legend__route-number">{route.number}</span>
          <span className="atlas-legend__route-label">{route.label}</span>
          <small>{route.marker}</small>
          {active === route.id && <em>Here</em>}
        </a>)}
      </nav>
      <div className="atlas-legend__subjects" aria-label="Subject route markers"><span className="atlas-legend__subject atlas-legend__subject--ga">GA</span><span className="atlas-legend__subject atlas-legend__subject--em">EM</span><span className="atlas-legend__subject atlas-legend__subject--dm">DM</span></div>
      <a className="atlas-legend__directory" href="/coverage?progress=near"><MapPinned size={14} /><span>Next route</span><strong>Below 100</strong></a>
      <div className="atlas-legend__scale"><Route size={13} aria-hidden="true" /><span>Verified / free</span></div>
    </aside>
  );
}
