/* STEAM Foundry reminder: keep the catalog provenance-first, dense but breathable, and easy to orient. */
/* STEAM Foundry catalog layer: keep initial discovery lightweight and defer dense country archives without altering source provenance or route semantics. */
import { catalogCountryIndex, csvChunkLoaders, lazyChunksByCountry } from "@/data/catalogIndex";

export type CatalogRow = {
  country: string;
  track: string;
  topic_tags: string;
  priority: string;
  source_type: string;
  source_title: string;
  source_url: string;
  resource_title: string;
  resource_url: string;
  resource_class: string;
  language: string;
  notes: string;
  access_model?: string;
  verification_status?: string;
  free_resource?: string;
};

function parseCsvLine(line: string) {
  const fields: string[] = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && quoted && next === '"') {
      field += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      fields.push(field);
      field = "";
    } else {
      field += char;
    }
  }
  fields.push(field);
  return fields;
}

function parseCsv(csv: string): CatalogRow[] {
  const normalized = csv.replace(/^\uFEFF/, "");
  const records: string[] = [];
  let record = "";
  let quoted = false;

  for (let index = 0; index < normalized.length; index += 1) {
    const char = normalized[index];
    const next = normalized[index + 1];

    if (char === '"' && quoted && next === '"') {
      record += '""';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
      record += char;
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (record.trim()) records.push(record);
      record = "";
      if (char === "\r" && next === "\n") index += 1;
    } else {
      record += char;
    }
  }

  if (record.trim()) records.push(record);
  if (!records.length) return [];

  const headers = parseCsvLine(records[0]!);
  return records.slice(1).map((line) => {
    const values = parseCsvLine(line);
    return headers.reduce((record, header, index) => {
      record[header as keyof CatalogRow] = values[index] ?? "";
      return record;
    }, {} as CatalogRow);
  });
}

export const dedupeByUrl = (rows: CatalogRow[]) => Array.from(new Map(rows.map((row) => [row.resource_url, row])).values());

/** Only http(s) links may render as anchors; data rows must never inject javascript: or data: URLs. */
export function safeExternalUrl(url: string): string | undefined {
  const trimmed = url.trim();
  return /^https?:\/\//i.test(trimmed) ? trimmed : undefined;
}

/** The explorer starts from index metadata while all resource CSVs are requested as lazy chunks. */
export const initialCatalog: CatalogRow[] = [];

const chunkCache = new Map<string, Promise<CatalogRow[]>>();

export const catalogCountries = Object.keys(catalogCountryIndex).sort((left, right) => left.localeCompare(right));
export const lazyCatalogChunkNames = Object.keys(csvChunkLoaders).sort((left, right) => left.localeCompare(right));

export function lazyChunksForCountries(countries: string[]) {
  return Array.from(new Set(countries.flatMap((country) => lazyChunksByCountry[country] ?? [])));
}

export async function loadCatalogChunks(chunkNames: string[]) {
  const rows = await Promise.all(chunkNames.map((name) => {
    const loader = csvChunkLoaders[name];
    if (!loader) {
      throw new Error(`Unknown catalog chunk: ${name}`);
    }
    if (!chunkCache.has(name)) {
      const load = loader().then((module) => parseCsv(module.default));
      load.catch(() => chunkCache.delete(name));
      chunkCache.set(name, load);
    }
    return chunkCache.get(name)!;
  }));
  return dedupeByUrl([...initialCatalog, ...rows.flat()]);
}

export const trackDefinitions = {
  GA: {
    label: "General Aptitude",
    short: "Reasoning, verbal, quantitative, and analytical practice.",
    color: "saffron",
  },
  EM: {
    label: "Engineering Mathematics",
    short: "Calculus, linear algebra, probability, and mathematical methods.",
    color: "teal",
  },
  DM: {
    label: "Discrete Mathematics",
    short: "Logic, combinatorics, graphs, algorithms, and structures.",
    color: "coral",
  },
  CS: {
    label: "Computer Science",
    short: "Algorithms, data structures, programming, and computational thinking.",
    color: "indigo",
  },
  S: {
    label: "Science",
    short: "Physics, chemistry, biology, and scientific reasoning.",
    color: "sky",
  },
  T: {
    label: "Technology",
    short: "Practical computing, tooling, and applied digital skills.",
    color: "slate",
  },
  E: {
    label: "Engineering",
    short: "Design, systems, and applied problem-solving practice.",
    color: "olive",
  },
  A: {
    label: "Arts",
    short: "Creative, spatial, and design-oriented thinking.",
    color: "rose",
  },
} as const;

export type TrackKey = keyof typeof trackDefinitions;

export const trackKeys: TrackKey[] = ["GA", "EM", "DM", "CS", "S", "T", "E", "A"];

export function rowTracks(row: CatalogRow): TrackKey[] {
  return trackKeys.filter((track) => row.track.split(/[\/, ]+/).includes(track));
}

export function hostFromUrl(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "official source";
  }
}

export function resourceKind(row: CatalogRow) {
  if (row.resource_class.includes("solution") || row.resource_class.includes("answer")) return "Solutions & answers";
  if (row.resource_class.includes("gateway")) return "Official gateway";
  if (row.resource_class.includes("practice")) return "Practice & quizzes";
  if (row.resource_class.includes("paper") || row.resource_class.includes("resource")) return "Papers & problems";
  return "Assignments & study";
}

export const resourceTypeOptions = ["All materials", "Exams", "Past year questions", "Contests", "Solutions", "Quizzes", "Olympiads", "Assignments", "MCQs"] as const;
export type ResourceType = typeof resourceTypeOptions[number];

export function resourceType(row: CatalogRow): Exclude<ResourceType, "All materials"> {
  const haystack = [row.resource_class, row.resource_title, row.source_title, row.topic_tags, row.notes].join(" ").toLowerCase();
  if (/(solution|answer key|answer sheet|worked answer|mark scheme)/.test(haystack)) return "Solutions";
  if (/(olympiad|mathematical olympiad|maths olympiad)/.test(haystack)) return "Olympiads";
  if (/(quiz|quizzes|trivia|knowledge check)/.test(haystack)) return "Quizzes";
  if (/(multiple choice|mcq|mcqs|objective questions?)/.test(haystack)) return "MCQs";
  if (/(assignment|coursework|problem set|homework|tutorial sheet)/.test(haystack)) return "Assignments";
  if (/(contest|competition|challenge|tournament|hackathon)/.test(haystack)) return "Contests";
  if (/(past year|previous year|past paper|previous paper|question paper|pyq|archive|yearly paper)/.test(haystack)) return "Past year questions";
  return "Exams";
}

export const sourceQualityOptions = ["All source quality", "First-party official", "University / academic", "Reputable supplemental", "Catalog / other"] as const;
export type SourceQuality = typeof sourceQualityOptions[number];

export function sourceQuality(row: CatalogRow): Exclude<SourceQuality, "All source quality"> {
  const haystack = [row.source_type, row.source_title, row.notes].join(" ").toLowerCase();
  if (row.priority === "A" && /(university|college|institute|faculty|school|academic|research)/.test(haystack)) return "University / academic";
  if (row.priority === "A") return "First-party official";
  if (row.priority === "B" || /(reputable|supplemental|international|mirror|hosted archive)/.test(haystack)) return "Reputable supplemental";
  return "Catalog / other";
}

export function lastVerifiedDate(row: CatalogRow) {
  const date = verifiedDate(row);
  if (!date) return "Not recorded";
  return new Intl.DateTimeFormat("en", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(date);
}

export function verifiedDate(row: CatalogRow) {
  const dateMatch = (row.verification_status ?? "").match(/\b20\d{2}-\d{2}-\d{2}\b/);
  if (!dateMatch) return null;
  const date = new Date(`${dateMatch[0]}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function verifiedWithinDays(row: CatalogRow, days: number) {
  const date = verifiedDate(row);
  if (!date) return false;
  const age = Date.now() - date.getTime();
  const day = 24 * 60 * 60 * 1000;
  return age >= -day && age <= days * day;
}

function sourceIsEnglish(row: CatalogRow) {
  return !row.language || /english/i.test(row.language);
}

export function displaySourceTitle(row: CatalogRow) {
  if (!sourceIsEnglish(row)) return `${row.source_type || "Official"} source — ${row.country}`;
  return row.source_title || `${row.source_type || "Official"} source`;
}

export function displayNotes(row: CatalogRow) {
  if (!sourceIsEnglish(row)) return `Verified ${resourceKind(row).toLowerCase()} from ${row.country}. The linked source is published in ${row.language}.`;
  return row.notes || "First-party archive record retained in the verified catalog.";
}

export function isFreeResource(row: CatalogRow) {
  return row.free_resource?.toLowerCase() === "yes";
}

export function accessLabel(row: CatalogRow) {
  if (!isFreeResource(row)) return "Access not classified";
  return row.access_model || "Free access";
}

export function verificationLabel(row: CatalogRow) {
  if (row.verification_status) return row.verification_status;
  return row.priority === "A" ? "First-party record" : "Catalog record";
}

export function hasAccessCaveat(row: CatalogRow) {
  return /access caveat/i.test(row.verification_status ?? "");
}

export function displayTitle(row: CatalogRow) {
  if (!sourceIsEnglish(row)) return `${resourceKind(row)} — ${row.country}`;
  const rawTitle = (row.resource_title || "").trim();
  const normalizedTitle = rawTitle
    .replace(/\.(pdf|docx?|xlsx?)$/i, "")
    .replace(/[_]+/g, " ")
    .replace(/[\[(]\s*\d+(?:\.\d+)?\s*(?:KB|MB|GB)\s*[\])]/gi, "")
    .replace(/\s*[-|–—]\s*\d+(?:\.\d+)?\s*(?:KB|MB|GB)\s*$/i, "")
    .replace(/\s+\d+(?:\.\d+)?\s*(?:KB|MB|GB)\b/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
  const looksLikeAssetName = !normalizedTitle
    || /^(?:\(?\d+(?:\.\d+)?\s*(?:KB|MB|GB)\)?|download|document|file|resource)[\s_-]*\d*$/i.test(normalizedTitle)
    || /^(?:[a-f0-9]{8,}|\d{4,})\.(?:pdf|docx?|xlsx?)$/i.test(rawTitle)
    || /^(?:download|document|file|resource)[\s_-]*\d+$/i.test(normalizedTitle);
  const looksLikeGenericLabel = /^(?:practice questions?|past papers?|previous papers?|exam papers?|questions?|solutions?|answer keys?|downloads?)$/i.test(normalizedTitle);
  const sourceTitle = row.source_title.trim();
  const sourceLooksGeneric = /^(?:official source|source|download|document|file|resource|practice questions?|past papers?|previous papers?|exam papers?|questions?|solutions?|answer keys?|downloads?)[\s_-]*\d*$/i.test(sourceTitle);
  const fallback = sourceTitle && !sourceLooksGeneric
    ? `${resourceKind(row)} — ${sourceTitle}`
    : `${resourceKind(row)} archive — ${row.country}`;
  const value = looksLikeAssetName || looksLikeGenericLabel ? fallback : normalizedTitle;
  return value.charAt(0).toUpperCase() + value.slice(1);
}
