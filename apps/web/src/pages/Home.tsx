/* STEAM Foundry reminder: make a large archive feel calm, directional, and trustworthy. */
/* STEAM Foundry explorer: an editorial field guide with asymmetric routes, quiet mineral surfaces, and provenance-led microcopy. */
/* STEAM Foundry explorer: retain the mineral-paper field-guide layout, editorial hierarchy, and visible provenance cues while data arrives progressively. */
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import {
  ArrowDownUp,
  ArrowUpRight,
  ArrowRight,
  Bookmark,
  Check,
  ChevronDown,
  CircleHelp,
  Download,
  Filter,
  Grid2X2,
  ListFilter,
  Menu,
  Printer,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Sparkles,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ResourceCard } from "@/components/ResourceCard";
import { AtlasLegend } from "@/components/AtlasLegend";
import { BangladeshSourceForm } from "@/components/BangladeshSourceForm";
import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "@/components/ui/pagination";
import { CatalogRow, TrackKey, accessLabel, catalogCountries, displayNotes, displaySourceTitle, displayTitle, hasAccessCaveat, initialCatalog, isFreeResource, lastVerifiedDate, lazyCatalogChunkNames, lazyChunksForCountries, loadCatalogChunks, resourceKind, resourceType, resourceTypeOptions, rowTracks, sourceQuality, sourceQualityOptions, trackDefinitions, trackKeys, verifiedWithinDays, verificationLabel } from "@/lib/catalog";
import { coverageIndex } from "@/lib/coverage";
import { REGION_BY_STATE, REGION_ORDER, Region } from "@/data/regions";
import { catalogIndexTotals } from "@/data/catalogIndex";

type FilterState = {
  query: string;
  track: "All" | TrackKey;
  country: string;
  region: "All regions" | Region;
  kind: string;
  type: typeof resourceTypeOptions[number];
  sourceQuality: typeof sourceQualityOptions[number];
  fresh: "All freshness" | FreshnessValue;
  freeOnly: boolean;
};

const freshnessOptions = [
  { value: "30", label: "30 days" },
  { value: "90", label: "90 days" },
  { value: "180", label: "180 days" },
  { value: "365", label: "1 year" },
] as const;
type FreshnessValue = typeof freshnessOptions[number]["value"];

const initialFilters: FilterState = { query: "", track: "All", country: "All countries", region: "All regions", kind: "All formats", type: "All materials", sourceQuality: "All source quality", fresh: "All freshness", freeOnly: false };
const catalogRegionAliases: Record<string, Region> = { Europe: "Europe", "Australia / New Zealand": "Oceania", "North America": "Americas", "Latin America": "Americas" };

function regionForCatalogCountry(country: string): Region | null {
  if (country in REGION_BY_STATE) return REGION_BY_STATE[country as keyof typeof REGION_BY_STATE];
  if (catalogRegionAliases[country]) return catalogRegionAliases[country];
  const regions = new Set(country.split("/").map((part) => REGION_BY_STATE[part.trim() as keyof typeof REGION_BY_STATE]).filter(Boolean));
  return regions.size === 1 ? Array.from(regions)[0] : null;
}

function filtersFromSearch(search: string): FilterState {
  const params = new URLSearchParams(search);
  const track = params.get("track");
  const country = params.get("country");
  const region = params.get("region");
  const fresh = params.get("fresh");
  return {
    query: params.get("q") ?? "",
    track: track && ["GA", "EM", "DM"].includes(track) ? track as FilterState["track"] : "All",
    country: country || "All countries",
    region: region && REGION_ORDER.includes(region as Region) ? region as Region : "All regions",
    kind: params.get("kind") || "All formats",
    type: resourceTypeOptions.includes(params.get("type") as FilterState["type"]) ? params.get("type") as FilterState["type"] : "All materials",
    sourceQuality: sourceQualityOptions.includes(params.get("quality") as FilterState["sourceQuality"]) ? params.get("quality") as FilterState["sourceQuality"] : "All source quality",
    fresh: freshnessOptions.some((option) => option.value === fresh) ? fresh as FreshnessValue : "All freshness",
    freeOnly: params.get("free") === "1",
  };
}

const featuredGateways = [
  { label: "GATE downloads", place: "India", note: "GA + Engineering Mathematics", url: "https://gate2026.iitg.ac.in/download.html" },
  { label: "CEMC past contests", place: "Canada", note: "Mathematics + computing", url: "https://cemc.uwaterloo.ca/resources/past-contests" },
  { label: "TMUA preparation", place: "United Kingdom", note: "Admissions mathematics", url: "https://esat-tmua.ac.uk/tmua-preparation-materials/" },
  { label: "IOI tasks", place: "Global", note: "Algorithms + solutions", url: "https://ioinformatics.org/page/ioi-2025/60" },
];

const prettyCount = (value: number) => new Intl.NumberFormat("en-US").format(value);
const PAGE_SIZE = 48;

function csvValue(value: string) {
  return `"${String(value ?? "").replace(/"/g, '""')}"`;
}

function downloadFilteredCsv(rows: CatalogRow[]) {
  const headers: Array<keyof CatalogRow> = ["country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url", "resource_title", "resource_url", "resource_class", "language", "notes", "access_model", "verification_status", "free_resource"];
  const content = [headers.join(","), ...rows.map((row) => headers.map((header) => csvValue(row[header] ?? "")).join(","))].join("\r\n");
  const blob = new Blob([`\uFEFF${content}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `steam-foundry-filtered-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function pageItems(currentPage: number, totalPages: number): Array<number | "ellipsis"> {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, index) => index + 1);
  const candidates = Array.from(new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1])).filter((value) => value > 0 && value <= totalPages).sort((a, b) => a - b);
  return candidates.reduce<Array<number | "ellipsis">>((items, value, index) => {
    if (index > 0 && value - candidates[index - 1] > 1) items.push("ellipsis");
    items.push(value);
    return items;
  }, []);
}

export default function Home() {
  const { user } = useAuth();

  const [filters, setFilters] = useState<FilterState>(() => filtersFromSearch(window.location.search));
  const [page, setPage] = useState(1);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const [selectedRow, setSelectedRow] = useState<CatalogRow | null>(null);
  const [sortBy, setSortBy] = useState<"relevance" | "country" | "title">("relevance");
  const [loadedCatalog, setLoadedCatalog] = useState<CatalogRow[]>(initialCatalog);
  const [isCatalogLoading, setIsCatalogLoading] = useState(true);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setSelectedRow(null);
      setIsMobileNavOpen(false);
      setIsFilterOpen(false);
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  useEffect(() => {
    document.body.classList.toggle("dialog-open", Boolean(selectedRow));
    return () => document.body.classList.remove("dialog-open");
  }, [selectedRow]);

  const countries = catalogCountries;
  const kinds = ["Assignments & study", "Official gateway", "Papers & problems", "Practice & quizzes", "Solutions & answers"];
  const requestedChunks = useMemo(() => {
    if (filters.country !== "All countries") return lazyChunksForCountries([filters.country]);
    if (filters.region !== "All regions") return lazyChunksForCountries(catalogCountries.filter((country) => regionForCatalogCountry(country) === filters.region));
    return lazyCatalogChunkNames;
  }, [filters.country, filters.region]);
  const requestedChunkKey = requestedChunks.join("|");

  useEffect(() => {
    let cancelled = false;
    setIsCatalogLoading(true);
    loadCatalogChunks(requestedChunks)
      .then((rows) => {
        if (!cancelled) setLoadedCatalog(rows);
      })
      .catch(() => {
        if (!cancelled) setLoadedCatalog(initialCatalog);
      })
      .finally(() => {
        if (!cancelled) setIsCatalogLoading(false);
      });
    return () => { cancelled = true; };
  }, [requestedChunkKey]);

  const filteredRows = useMemo(() => {
    const normalizedQuery = filters.query.trim().toLowerCase();
    const result = loadedCatalog.filter((row) => {
      const matchesTrack = filters.track === "All" || rowTracks(row).includes(filters.track);
      const matchesCountry = filters.country === "All countries" || row.country === filters.country;
      const matchesRegion = filters.region === "All regions" || regionForCatalogCountry(row.country) === filters.region;
      const matchesKind = filters.kind === "All formats" || resourceKind(row) === filters.kind;
      const matchesType = filters.type === "All materials" || resourceType(row) === filters.type;
      const matchesQuality = filters.sourceQuality === "All source quality" || sourceQuality(row) === filters.sourceQuality;
      const matchesFresh = filters.fresh === "All freshness" || verifiedWithinDays(row, Number(filters.fresh));
      const matchesFree = !filters.freeOnly || isFreeResource(row);
      const haystack = [row.resource_title, row.source_title, row.country, row.track, row.notes, row.language].join(" ").toLowerCase();
      return matchesTrack && matchesCountry && matchesRegion && matchesKind && matchesType && matchesQuality && matchesFresh && matchesFree && (!normalizedQuery || haystack.includes(normalizedQuery));
    });
    return [...result].sort((a, b) => {
      if (sortBy === "country") return a.country.localeCompare(b.country) || a.resource_title.localeCompare(b.resource_title);
      if (sortBy === "title") return a.resource_title.localeCompare(b.resource_title);
      return Number(b.priority === "A") - Number(a.priority === "A") || a.resource_title.localeCompare(b.resource_title);
    });
  }, [filters, loadedCatalog, sortBy]);

  const trackCounts = catalogIndexTotals.trackCounts;

  const coverageStats = useMemo(() => {
    const freeMemberStates = coverageIndex.filter((entry) => entry.status !== "pending");
    return {
      freeRows: catalogIndexTotals.freeCount,
      freeMemberStates: freeMemberStates.length,
      pendingMemberStates: Math.max(0, 193 - freeMemberStates.length),
      baseMemberStates: coverageIndex.filter((entry) => entry.catalogCount > 0).length,
      caveatCount: coverageIndex.reduce((sum, entry) => sum + entry.caveatCount, 0),
      progress: Math.max(1, Math.round((freeMemberStates.length / 193) * 100)),
    };
  }, []);

  const sourceCount = catalogIndexTotals.sourceCount;
  const gatewayCount = catalogIndexTotals.gatewayCount;
  const activeFilterCount = [filters.track !== "All", filters.country !== "All countries", filters.region !== "All regions", filters.kind !== "All formats", filters.type !== "All materials", filters.sourceQuality !== "All source quality", filters.fresh !== "All freshness", filters.freeOnly, Boolean(filters.query)].filter(Boolean).length;
  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const visibleRows = filteredRows.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  const activeRouteLabel = filters.country !== "All countries"
    ? filters.country
    : filters.region !== "All regions"
      ? filters.region
      : filters.track !== "All"
        ? trackDefinitions[filters.track].label
        : filters.type !== "All materials"
        ? `${filters.type} materials`
        : filters.sourceQuality !== "All source quality"
          ? `${filters.sourceQuality} sources`
        : filters.query
          ? `“${filters.query}”`
          : "the global index";
  const hasRouteContext = activeFilterCount > 0;
  const browseRouteLabel = activeRouteLabel.startsWith("the ") ? activeRouteLabel : `the ${activeRouteLabel}`;
  const routeContextType = filters.country !== "All countries"
    ? "Country field note"
    : filters.region !== "All regions"
      ? "Regional field note"
      : filters.track !== "All"
        ? "Subject field note"
        : filters.type !== "All materials"
          ? "Material field note"
        : filters.sourceQuality !== "All source quality"
          ? "Source-quality field note"
        : "Search field note";

  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.query) params.set("q", filters.query);
    if (filters.track !== "All") params.set("track", filters.track);
    if (filters.country !== "All countries") params.set("country", filters.country);
    if (filters.region !== "All regions") params.set("region", filters.region);
    if (filters.kind !== "All formats") params.set("kind", filters.kind);
    if (filters.type !== "All materials") params.set("type", filters.type);
    if (filters.sourceQuality !== "All source quality") params.set("quality", filters.sourceQuality);
    if (filters.fresh !== "All freshness") params.set("fresh", filters.fresh);
    if (filters.freeOnly) params.set("free", "1");
    const query = params.toString();
    window.history.replaceState(null, "", `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`);
  }, [filters]);

  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(1);
  };

  const clearFilters = () => {
    setFilters(initialFilters);
    setPage(1);
  };

  return (
    <div className="site-shell">
      <header className="site-header">
        <a className="brand-lockup" href="#top" aria-label="STEAM Foundry home">
          <img src="steam-foundry-mark.svg" alt="" className="brand-mark" />
          <span><strong>STEAM</strong> Foundry</span>
        </a>
          <nav id="site-navigation" className={`header-nav ${isMobileNavOpen ? "header-nav--open" : ""}`} aria-label="Main navigation">
          <a href="#explore" onClick={() => setIsMobileNavOpen(false)}>Explore</a>
          <a href="#subjects" onClick={() => setIsMobileNavOpen(false)}>Subjects</a>
          <a href="/coverage" onClick={() => setIsMobileNavOpen(false)}>Country directory</a>
          <a href="#about" onClick={() => setIsMobileNavOpen(false)}>About the archive</a>
          {user?.role === "admin" && <a href="/review" onClick={() => setIsMobileNavOpen(false)}>Review queue</a>}
        </nav>
        <div className="header-actions">
          <span className="live-status"><span /> {isCatalogLoading ? "Loading archive" : "Archive ready"} · {prettyCount(catalogIndexTotals.catalogCount)} records</span>
          <Button variant="outline" size="sm" className="header-button" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })}>
            Browse archive <ArrowRight size={15} />
          </Button>
          <button type="button" className="mobile-menu" aria-label={isMobileNavOpen ? "Close navigation" : "Open navigation"} aria-expanded={isMobileNavOpen} aria-controls="site-navigation" onClick={() => setIsMobileNavOpen((open) => !open)}><Menu size={20} /></button>
        </div>
      </header>

      <AtlasLegend active="field" />

      <main id="top">
        <section className="hero-section">
          <div className="hero-backdrop" aria-hidden="true" />
          <div className="hero-inner">
            <div className="hero-copy">
              <p className="eyebrow eyebrow--light"><span className="eyebrow-marker coordinate-marker" /> A provenance-first practice archive</p>
              <h1>Find the next<br /><em>hard question.</em></h1>
              {hasRouteContext && <div className="hero-route-context" aria-label={`Active route: ${activeRouteLabel}`}><span>{routeContextType}</span><strong>{activeRouteLabel}</strong><small>{prettyCount(filteredRows.length)} matching records · route state preserved in the URL</small></div>}
              <p className="hero-description">A living field guide to General Aptitude, Mathematics, Computer Science, and the wider Science, Technology, Engineering, Arts, and Mathematics resources from exam bodies, universities, and contest organizers around the world.</p>
              <form className="hero-search" onSubmit={(event) => { event.preventDefault(); document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" }); }}>
                <Search size={19} />
                <input aria-label="Search the archive" value={filters.query} onChange={(event) => updateFilter("query", event.target.value)} placeholder="Search exams, contests, universities…" />
                <button type="submit">Search <ArrowRight size={16} /></button>
              </form>
              <div className="hero-quicklinks" aria-label="Quick browse links">
                <span>Quick browse</span>
                {trackKeys.map((track) => <button key={track} onClick={() => { updateFilter("track", track); document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" }); }}>{track} <ArrowUpRightIcon /></button>)}
              </div>
            </div>
            <div className="hero-note" aria-label="Archive note">
              <div className="hero-note__top"><span>Field note / 014</span><Sparkles size={15} /></div>
              <div className="hero-note__diagram"><span className="node node--one" /><span className="node node--two" /><span className="node node--three" /><span className="route route--one" /><span className="route route--two" /><span className="route route--three" /></div>
              <p>Start with a subject. Follow the source trail. Keep the good questions.</p>
              <div className="hero-note__footer"><span>STEAM Foundry</span><span>14.08.26</span></div>
            </div>
          </div>
          <div className="hero-scroll-cue"><span /> Scroll to explore</div>
        </section>

        <section className="stats-strip" aria-label="Archive statistics">
          <div className="stat-item"><span className="stat-number">{prettyCount(catalogIndexTotals.catalogCount)}</span><span className="stat-label">catalog records</span></div>
          <div className="stat-item"><span className="stat-number">{countries.length}</span><span className="stat-label">country tracks</span></div>
          <div className="stat-item"><span className="stat-number">{sourceCount}</span><span className="stat-label">source gateways</span></div>
          <div className="stat-item"><span className="stat-number">{gatewayCount}</span><span className="stat-label">official entry points</span></div>
          <div className="stats-statement">Built for the moments when<br /><strong>“more practice”</strong> is not specific enough.</div>
        </section>

        <section id="subjects" className="section section-subjects">
          <div className="section-heading section-heading--split">
            <div><p className="eyebrow"><span className="eyebrow-marker coordinate-marker" /> The subject system</p><h2>Routes into<br /><em>the archive.</em></h2></div>
            <p className="section-intro">The catalog groups resources by the kind of thinking they train. Move between mathematics, computer science, and the wider STEAM tracks, then narrow by country, exam family, or format.</p>
          </div>
          <div className="subject-grid">
            {trackKeys.map((track) => {
              const definition = trackDefinitions[track];
              return <button key={track} className={`subject-card subject-card--${track.toLowerCase()}`} onClick={() => { updateFilter("track", track); document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" }); }}>
                <div className="subject-card__image" aria-hidden="true"><span className="subject-card__monogram">{track}</span></div>
                <div className="subject-card__content"><div className="subject-card__index">0{trackKeys.indexOf(track) + 1} / {track}</div><h3>{definition.label}</h3><p>{definition.short}</p><div className="subject-card__footer"><span>{prettyCount(trackCounts[track])} resources</span><span className="circle-arrow"><ArrowUpRightIcon /></span></div></div>
              </button>;
            })}
          </div>
        </section>

          <section id="explore" className="section explorer-section">
          <div className="section-heading section-heading--explorer"><div><p className="eyebrow"><span className="eyebrow-marker coordinate-marker" /> The live index</p><h2>{hasRouteContext ? <>Browse <em>{browseRouteLabel} field</em>.</> : <>Browse the field.</>}</h2></div><p className="section-intro">Every result keeps its source trail visible. No filler, no invented counts—just links you can follow and verify.</p></div>
          <div className="coverage-panel" aria-label="Free-resource country coverage status">
            <div className="coverage-panel__intro"><div><p className="eyebrow eyebrow--muted">Coverage ledger</p><h3>{coverageStats.freeMemberStates} of 193 member states have free-tranche records.</h3><p>STEAM Foundry keeps pending countries visible instead of filling gaps with invented entries.</p></div><span className="coverage-panel__percent">{coverageStats.progress}%</span></div>
            <div className="coverage-meter" aria-hidden="true"><span style={{ width: `${coverageStats.progress}%` }} /></div>
            <div className="coverage-panel__stats"><span><strong>{coverageStats.freeRows}</strong> free records</span><span><strong>{coverageStats.baseMemberStates}</strong> base catalog labels</span><span><strong>{coverageStats.pendingMemberStates}</strong> states pending expansion</span><span className="coverage-panel__caveat"><strong>{coverageStats.caveatCount}</strong> access caveats</span><a className="coverage-panel__link" href="/coverage">Open the 193-state directory <ArrowUpRight size={14} /></a></div>
          </div>
          {filters.country !== "All countries" && <BangladeshSourceForm country={filters.country} />}
          <div className="explorer-toolbar-mobile"><Button variant="outline" className="filter-toggle" aria-expanded={isFilterOpen} aria-controls="filter-rail" onClick={() => setIsFilterOpen((open) => !open)}><SlidersHorizontal size={17} /> Filters {activeFilterCount > 0 && <span className="filter-count">{activeFilterCount}</span>}</Button><span>{prettyCount(filteredRows.length)} results</span></div>
          <div className="explorer-layout">
            <aside id="filter-rail" className={`filter-rail ${isFilterOpen ? "filter-rail--open" : ""}`}>
              <div className="filter-rail__header"><div><span className="eyebrow eyebrow--muted"><span className="eyebrow-marker coordinate-marker" /> Atlas rail / index controls</span><h3>Find your route</h3></div><button className="filter-close" onClick={() => setIsFilterOpen(false)} aria-label="Close filters"><X size={18} /></button></div>
              <div className="filter-rail__route" aria-label="Subject route legend"><span className="filter-rail__route-line" />{trackKeys.map((track) => <span key={track} className={`rail-route rail-route--${track.toLowerCase()}`}>{track}</span>)}</div>
              <div className="filter-group"><label>Subject / route</label><div className="segmented-control">{["All", ...trackKeys].map((value) => <button key={value} type="button" aria-pressed={filters.track === value} className={`${filters.track === value ? "is-active" : ""} ${value !== "All" ? `track-filter--${value.toLowerCase()}` : ""}`} onClick={() => updateFilter("track", value as FilterState["track"])}>{value}</button>)}</div></div>
              <div className="filter-group"><label htmlFor="country-filter">Country</label><div className="select-wrap"><select id="country-filter" value={filters.country} onChange={(event) => updateFilter("country", event.target.value)}><option>All countries</option>{countries.map((country) => <option key={country}>{country}</option>)}</select><ChevronDown size={15} /></div></div>
              <div className="filter-group"><label htmlFor="region-filter">Region</label><div className="select-wrap"><select id="region-filter" value={filters.region} onChange={(event) => updateFilter("region", event.target.value as FilterState["region"])}><option>All regions</option>{REGION_ORDER.map((region) => <option key={region}>{region}</option>)}</select><ChevronDown size={15} /></div></div>
              <div className="filter-group"><label htmlFor="kind-filter">Resource format</label><div className="select-wrap"><select id="kind-filter" value={filters.kind} onChange={(event) => updateFilter("kind", event.target.value)}><option>All formats</option>{kinds.map((kind) => <option key={kind}>{kind}</option>)}</select><ChevronDown size={15} /></div></div>
              <div className="filter-group"><label>Material type</label><div className="resource-type-filters" role="group" aria-label="Filter by material type">{resourceTypeOptions.map((type) => <button key={type} type="button" aria-pressed={filters.type === type} className={filters.type === type ? "is-active" : ""} onClick={() => updateFilter("type", type)}>{type === "Past year questions" ? "PYQs" : type}</button>)}</div><p className="filter-help">Find a specific practice format without losing the source trail.</p></div>
              <div className="filter-group"><label htmlFor="quality-filter">Source quality</label><div className="select-wrap"><select id="quality-filter" value={filters.sourceQuality} onChange={(event) => updateFilter("sourceQuality", event.target.value as FilterState["sourceQuality"])}><option>All source quality</option>{sourceQualityOptions.slice(1).map((quality) => <option key={quality}>{quality}</option>)}</select><ChevronDown size={15} /></div><p className="filter-help">Separate official, academic, supplemental, and other records.</p></div>
              <div className="filter-group"><label htmlFor="freshness-filter">Verified within</label><div className="select-wrap"><select id="freshness-filter" value={filters.fresh} onChange={(event) => updateFilter("fresh", event.target.value as FilterState["fresh"])}><option>All freshness</option>{freshnessOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select><ChevronDown size={15} /></div><p className="filter-help">Use the recorded verification date, not the source publication date.</p></div>
              <div className="filter-group filter-group--free"><label className="free-filter"><input type="checkbox" checked={filters.freeOnly} onChange={(event) => updateFilter("freeOnly", event.target.checked)} /><span className="free-filter__box" /><span>Free resources only</span></label><p>Open access, no paid subscription required.</p></div>
              <div className="filter-group filter-group--search"><label htmlFor="archive-search">Keywords</label><div className="filter-input"><Search size={16} /><Input id="archive-search" value={filters.query} onChange={(event) => updateFilter("query", event.target.value)} placeholder="Try “olympiad”" /></div></div>
              <button className="reset-button" onClick={clearFilters}><RotateCcw size={14} /> Reset all filters</button>
              <div className="filter-rail__legend"><p className="eyebrow eyebrow--muted">Reading the index</p><p><span className="legend-dot legend-dot--official" /> Official gateway</p><p><span className="legend-dot legend-dot--paper" /> Paper, practice, or problem</p><p><span className="legend-dot legend-dot--solution" /> Solution or answer key</p></div>
            </aside>

            <div className="results-pane">
              <div className="results-header"><div><p className="results-count"><span className="results-orientation"><span className="coordinate-marker" /> {filters.track === "All" ? "All subjects" : filters.track} / {filters.country !== "All countries" ? filters.country : filters.region !== "All regions" ? filters.region : "Global index"}</span><strong aria-live="polite">{prettyCount(filteredRows.length)}</strong> matching records</p><div className="results-subject-legend" aria-label="Persistent subject route legend"><span>Routes</span>{trackKeys.map((track) => <button key={track} type="button" aria-pressed={filters.track === track} className={`results-subject-legend__route results-subject-legend__route--${track.toLowerCase()} ${filters.track === track ? "is-active" : ""}`} onClick={() => updateFilter("track", filters.track === track ? "All" : track)}><i>{track}</i>{trackDefinitions[track].label}</button>)}</div><div className="active-filters">{filters.track !== "All" && <button onClick={() => updateFilter("track", "All")}>{filters.track} <X size={12} /></button>}{filters.country !== "All countries" && <button onClick={() => updateFilter("country", "All countries")}>{filters.country} <X size={12} /></button>}{filters.region !== "All regions" && <button onClick={() => updateFilter("region", "All regions")}>{filters.region} <X size={12} /></button>}{filters.kind !== "All formats" && <button onClick={() => updateFilter("kind", "All formats")}>{filters.kind} <X size={12} /></button>}{filters.type !== "All materials" && <button onClick={() => updateFilter("type", "All materials")}>{filters.type === "Past year questions" ? "PYQs" : filters.type} <X size={12} /></button>}{filters.sourceQuality !== "All source quality" && <button onClick={() => updateFilter("sourceQuality", "All source quality")}>{filters.sourceQuality} <X size={12} /></button>}{filters.fresh !== "All freshness" && <button onClick={() => updateFilter("fresh", "All freshness")}>Verified within {freshnessOptions.find((option) => option.value === filters.fresh)?.label} <X size={12} /></button>}{filters.freeOnly && <button onClick={() => updateFilter("freeOnly", false)}>Free only <X size={12} /></button>}{filters.query && <button onClick={() => updateFilter("query", "")}>“{filters.query}” <X size={12} /></button>}</div></div><div className="results-actions"><button className="export-button" type="button" onClick={() => downloadFilteredCsv(filteredRows)} title="Download all matching records as CSV"><Download size={15} /> Export CSV</button><button className="export-button" type="button" onClick={() => window.print()} title="Print or save the filtered view as PDF"><Printer size={15} /> Print / PDF</button><button className="view-toggle is-active" aria-label="Grid view"><Grid2X2 size={16} /></button><button className="view-toggle" aria-label="List view"><ListFilter size={16} /></button><div className="sort-wrap"><ArrowDownUp size={14} /><select aria-label="Sort results" value={sortBy} onChange={(event) => { setSortBy(event.target.value as typeof sortBy); setPage(1); }}><option value="relevance">Best match</option><option value="country">Country A–Z</option><option value="title">Title A–Z</option></select></div></div></div>
              {filteredRows.length > 0 ? <><div className="resource-grid">{visibleRows.map((row, index) => <ResourceCard key={`${row.resource_url}-${index}`} row={row} onInspect={setSelectedRow} index={index} />)}</div><div className="catalog-pagination-wrap"><Pagination><PaginationContent><PaginationItem><PaginationPrevious href="#explore" aria-disabled={currentPage === 1} tabIndex={currentPage === 1 ? -1 : undefined} onClick={(event) => { event.preventDefault(); if (currentPage > 1) { setPage(currentPage - 1); document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" }); } }} /></PaginationItem>{pageItems(currentPage, totalPages).map((item, index) => item === "ellipsis" ? <PaginationItem key={`ellipsis-${index}`}><PaginationEllipsis /></PaginationItem> : <PaginationItem key={item}><PaginationLink href="#explore" isActive={item === currentPage} aria-label={`Go to page ${item}`} onClick={(event) => { event.preventDefault(); setPage(item); document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" }); }}>{item}</PaginationLink></PaginationItem>)}<PaginationItem><PaginationNext href="#explore" aria-disabled={currentPage === totalPages} tabIndex={currentPage === totalPages ? -1 : undefined} onClick={(event) => { event.preventDefault(); if (currentPage < totalPages) { setPage(currentPage + 1); document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" }); } }} /></PaginationItem></PaginationContent></Pagination><span className="catalog-pagination__meta"><span className="pagination-route"><span className="coordinate-marker" /> Route / {activeRouteLabel}</span><span>Showing {(currentPage - 1) * PAGE_SIZE + 1}–{Math.min(currentPage * PAGE_SIZE, filteredRows.length)} of {prettyCount(filteredRows.length)} records · Page {currentPage} of {totalPages}</span></span></div></> : <div className="empty-state"><div className="empty-state__icon"><CircleHelp size={25} /></div><h3>No route found yet.</h3><p>Try a broader keyword, switch subject, or reset the filters to see the full index.</p><Button variant="outline" onClick={clearFilters}>Reset the route</Button></div>}
            </div>
          </div>
        </section>

        <section className="print-export-sheet" aria-labelledby="print-export-title">
          <div className="print-export-sheet__header"><p className="eyebrow">STEAM Foundry / filtered export</p><h2 id="print-export-title">{prettyCount(filteredRows.length)} matching records</h2><p>Generated from the current explorer filters on {new Intl.DateTimeFormat("en", { dateStyle: "long" }).format(new Date())}.</p></div>
          <table><thead><tr><th>Title</th><th>Country</th><th>Subject</th><th>Material</th><th>Source</th><th>Last verified</th><th>Public URL</th></tr></thead><tbody>{filteredRows.map((row) => <tr key={`print-${row.resource_url}`}><td>{displayTitle(row)}</td><td>{row.country}</td><td>{row.track}</td><td>{resourceType(row)}</td><td>{displaySourceTitle(row)}</td><td>{lastVerifiedDate(row)}</td><td>{row.resource_url}</td></tr>)}</tbody></table>
        </section>

        <section className="section gateway-section">
          <div className="gateway-copy"><p className="eyebrow"><span className="eyebrow-marker coordinate-marker" /> Start with the source</p><h2>Go straight to<br /><em>the good desks.</em></h2><p>These official entry points are the fastest way to orient yourself inside a large archive. Use the filters above when you want a more specific path.</p><a href="#explore" className="text-link">Return to the live index <ArrowRight size={16} /></a></div>
          <div className="gateway-list">{featuredGateways.map((gateway, index) => <a className="gateway-row" key={gateway.label} href={gateway.url} target="_blank" rel="noreferrer"><span className="gateway-row__index">0{index + 1}</span><span className="gateway-row__main"><strong>{gateway.label}</strong><small>{gateway.place} · {gateway.note}</small><span className="gateway-row__route">Source trail / official entry point</span></span><ArrowUpRight size={17} /></a>)}</div>
        </section>

        <section id="about" className="about-band"><div className="about-band__mark"><Bookmark size={22} /></div><div><p className="eyebrow eyebrow--light"><span className="eyebrow-marker coordinate-marker" /> Why this archive exists</p><h2>More practice is easy.<br /><em>Better practice is the work.</em></h2></div><p>STEAM Foundry is a navigational layer over a scattered world of official exam archives, contest problem sets, university assignments, and solution collections. It reports the record honestly, keeps provenance visible, and gives you a clear next move.</p></section>
      </main>

      <footer className="site-footer"><a className="brand-lockup" href="#top"><img src="steam-foundry-mark.svg" alt="" className="brand-mark" /><span><strong>STEAM</strong> Foundry</span></a><span className="site-footer__routes" aria-label="STEAM Foundry subject routes">{trackKeys.map((track) => <span key={track} className={`site-footer__route site-footer__route--${track.toLowerCase()}`}><i /> {track}</span>)}</span><a className="site-footer__coverage-link" href="/coverage">Country directory <ArrowRight size={13} /></a><span>Built for curious learners</span></footer>

      {selectedRow && <div className="dialog-scrim" role="presentation" onClick={() => setSelectedRow(null)}><section className="resource-dialog" role="dialog" aria-modal="true" aria-labelledby="resource-dialog-title" aria-describedby="resource-dialog-note" tabIndex={-1} onClick={(event) => event.stopPropagation()}><button type="button" className="dialog-close" onClick={() => setSelectedRow(null)} aria-label="Close resource details"><X size={20} /></button><p className="eyebrow"><span className="eyebrow-marker coordinate-marker" /> Resource inspection</p><div className="dialog-tags">{rowTracks(selectedRow).map((track) => <span key={track} className={`track-chip track-chip--${track.toLowerCase()}`}>{track}</span>)}<span className="official-pill"><Check size={13} /> {selectedRow.priority === "A" ? "First-party source" : "Catalog source"}</span>{isFreeResource(selectedRow) && <span className="free-pill"><Check size={13} /> Free access</span>}{hasAccessCaveat(selectedRow) && <span className="caveat-pill" title={verificationLabel(selectedRow)}>Access caveat</span>}</div><h2 id="resource-dialog-title">{displayTitle(selectedRow)}</h2><p className="dialog-source">{displaySourceTitle(selectedRow)}</p><div className="dialog-meta"><div><span>Country / region</span><strong>{selectedRow.country}</strong></div><div><span>Format</span><strong>{resourceKind(selectedRow)}</strong></div><div><span>Material type</span><strong>{resourceType(selectedRow)}</strong></div><div><span>Source quality</span><strong>{sourceQuality(selectedRow)}</strong></div><div><span>Language</span><strong>{selectedRow.language || "English"}</strong></div><div><span>Source type</span><strong>{selectedRow.source_type || "Official archive"}</strong></div><div><span>Access</span><strong className={hasAccessCaveat(selectedRow) ? "dialog-status--warning" : ""}>{isFreeResource(selectedRow) ? accessLabel(selectedRow) : "Not classified"}</strong></div><div><span>Last verified</span><strong>{lastVerifiedDate(selectedRow)}</strong></div></div><div className="dialog-note" id="resource-dialog-note"><span className="eyebrow eyebrow--muted">Archive note</span><p>{displayNotes(selectedRow) || "This record is retained because it points to a substantive, publicly reachable source in the verified catalog."}</p></div><a className="dialog-open" href={selectedRow.resource_url} target="_blank" rel="noreferrer">Open source <ArrowUpRight size={17} /></a></section></div>}
    </div>
  );
}

function ArrowUpRightIcon() { return <ArrowUpRight size={15} />; }
