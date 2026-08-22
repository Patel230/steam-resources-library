/* STEAM Foundry reminder: keep the catalog provenance-first, dense but breathable, and easy to orient. */
/* STEAM Foundry catalog layer: keep initial discovery lightweight and defer dense country archives without altering source provenance or route semantics. */
import { catalogCountryIndex, lazyChunksByCountry } from "@/data/catalogIndex";

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

  const headers = parseCsvLine(records[0]);
  return records.slice(1).map((line) => {
    const values = parseCsvLine(line);
    return headers.reduce((record, header, index) => {
      record[header as keyof CatalogRow] = values[index] ?? "";
      return record;
    }, {} as CatalogRow);
  });
}

export const dedupeByUrl = (rows: CatalogRow[]) => Array.from(new Map(rows.map((row) => [row.resource_url, row])).values());

/** The explorer starts from index metadata while all resource CSVs are requested as lazy chunks. */
export const initialCatalog: CatalogRow[] = [];

const csvChunkLoaders: Record<string, () => Promise<{ default: string }>> = {
  "free_resources.csv": () => import("@/data/free_resources.csv?raw"),
  "important_country_resources.csv": () => import("@/data/important_country_resources.csv?raw"),
  "european_wave_resources.csv": () => import("@/data/european_wave_resources.csv?raw"),
  "next_european_wave_resources.csv": () => import("@/data/next_european_wave_resources.csv?raw"),
  "south_southeast_asia_resources.csv": () => import("@/data/south_southeast_asia_resources.csv?raw"),
  "active_country_depth_resources.csv": () => import("@/data/active_country_depth_resources.csv?raw"),
  "archive_depth_resources.csv": () => import("@/data/archive_depth_resources.csv?raw"),
  "four_country_depth_resources.csv": () => import("@/data/four_country_depth_resources.csv?raw"),
  "india_gate_verified_resources.csv": () => import("@/data/india_gate_verified_resources.csv?raw"),
  "india_tifr_verified_resources.csv": () => import("@/data/india_tifr_verified_resources.csv?raw"),
  "canada_cemc_bcc_2025_verified_resources.csv": () => import("@/data/canada_cemc_bcc_2025_verified_resources.csv?raw"),
  "canada_cemc_verified_resources.csv": () => import("@/data/canada_cemc_verified_resources.csv?raw"),
  "germany_bwinf_verified_resources.csv": () => import("@/data/germany_bwinf_verified_resources.csv?raw"),
  "france_ccinp_verified_resources.csv": () => import("@/data/france_ccinp_verified_resources.csv?raw"),
  "japan_mext_verified_resources.csv": () => import("@/data/japan_mext_verified_resources.csv?raw"),
  "japan_joi_verified_resources.csv": () => import("@/data/japan_joi_verified_resources.csv?raw"),
  "united_kingdom_bmo_verified_resources.csv": () => import("@/data/united_kingdom_bmo_verified_resources.csv?raw"),
  "south_africa_computer_olympiad_verified_resources.csv": () => import("@/data/south_africa_computer_olympiad_verified_resources.csv?raw"),
  "south_africa_foundation_math_verified_resources.csv": () => import("@/data/south_africa_foundation_math_verified_resources.csv?raw"),
  "south_africa_junior_math_verified_resources.csv": () => import("@/data/south_africa_junior_math_verified_resources.csv?raw"),
  "south_africa_uj_math_verified_resources.csv": () => import("@/data/south_africa_uj_math_verified_resources.csv?raw"),
  "south_africa_uj_math_followup_verified_resources.csv": () => import("@/data/south_africa_uj_math_followup_verified_resources.csv?raw"),
  "south_africa_uct_2018_verified_resources.csv": () => import("@/data/south_africa_uct_2018_verified_resources.csv?raw"),
  "south_africa_upmc_verified_resources.csv": () => import("@/data/south_africa_upmc_verified_resources.csv?raw"),
  "south_africa_wits_verified_resources.csv": () => import("@/data/south_africa_wits_verified_resources.csv?raw"),
  "south_africa_samf_verified_resources.csv": () => import("@/data/south_africa_samf_verified_resources.csv?raw"),
  "nigeria_waec_verified_resources.csv": () => import("@/data/nigeria_waec_verified_resources.csv?raw"),
  "new_zealand_nzqa_verified_resources.csv": () => import("@/data/new_zealand_nzqa_verified_resources.csv?raw"),
  "united_states_usaco_verified_resources.csv": () => import("@/data/united_states_usaco_verified_resources.csv?raw"),
  "united_states_usaco_2026_verified_resources.csv": () => import("@/data/united_states_usaco_2026_verified_resources.csv?raw"),
  "brazil_obm_verified_resources.csv": () => import("@/data/brazil_obm_verified_resources.csv?raw"),
  "italy_math_olympiad_verified_resources.csv": () => import("@/data/italy_math_olympiad_verified_resources.csv?raw"),
  "netherlands_math_olympiad_verified_resources.csv": () => import("@/data/netherlands_math_olympiad_verified_resources.csv?raw"),
  "austria_oemo_verified_resources.csv": () => import("@/data/austria_oemo_verified_resources.csv?raw"),
  "australia_scsa_verified_resources.csv": () => import("@/data/australia_scsa_verified_resources.csv?raw"),
  "australia_scsa_2022_2025_verified_resources.csv": () => import("@/data/australia_scsa_2022_2025_verified_resources.csv?raw"),
  "australia_nesa_2020_2023_verified_resources.csv": () => import("@/data/australia_nesa_2020_2023_verified_resources.csv?raw"),
  "australia_nesa_2016_2019_verified_resources.csv": () => import("@/data/australia_nesa_2016_2019_verified_resources.csv?raw"),
  "australia_nesa_2015_verified_resources.csv": () => import("@/data/australia_nesa_2015_verified_resources.csv?raw"),
  "australia_nesa_2014_mg_verified_resources.csv": () => import("@/data/australia_nesa_2014_mg_verified_resources.csv?raw"),
  "australia_nesa_2015_ext_verified_resources.csv": () => import("@/data/australia_nesa_2015_ext_verified_resources.csv?raw"),
  "australia_amt_verified_resources.csv": () => import("@/data/australia_amt_verified_resources.csv?raw"),
  "australia_amt_enrichment_verified_resources.csv": () => import("@/data/australia_amt_enrichment_verified_resources.csv?raw"),
  "australia_qcaa_2025_verified_resources.csv": () => import("@/data/australia_qcaa_2025_verified_resources.csv?raw"),
  "australia_qcaa_2023_2025_verified_resources.csv": () => import("@/data/australia_qcaa_2023_2025_verified_resources.csv?raw"),
  "australia_vcaa_2023_2025_verified_resources.csv": () => import("@/data/australia_vcaa_2023_2025_verified_resources.csv?raw"),
  "australia_vcaa_guides_verified_resources.csv": () => import("@/data/australia_vcaa_guides_verified_resources.csv?raw"),
  "republic_of_korea_kice_csat_verified_resources.csv": () => import("@/data/republic_of_korea_kice_csat_verified_resources.csv?raw"),
  "china_ccf_gesp_verified_resources.csv": () => import("@/data/china_ccf_gesp_verified_resources.csv?raw"),
  "mexico_omm_canguro_verified_resources.csv": () => import("@/data/mexico_omm_canguro_verified_resources.csv?raw"),
  "pakistan_pu_verified_resources.csv": () => import("@/data/pakistan_pu_verified_resources.csv?raw"),
  "pakistan_iba_verified_resources.csv": () => import("@/data/pakistan_iba_verified_resources.csv?raw"),
  "pakistan_university_followup_verified_resources.csv": () => import("@/data/pakistan_university_followup_verified_resources.csv?raw"),
  "pakistan_giki_verified_resources.csv": () => import("@/data/pakistan_giki_verified_resources.csv?raw"),
  "pakistan_gcu_verified_resources.csv": () => import("@/data/pakistan_gcu_verified_resources.csv?raw"),
  "turkiye_tubitak_verified_resources.csv": () => import("@/data/turkiye_tubitak_verified_resources.csv?raw"),
  "russia_fipi_advanced_math_verified_resources.csv": () => import("@/data/russia_fipi_advanced_math_verified_resources.csv?raw"),
  "poland_om_verified_resources.csv": () => import("@/data/poland_om_verified_resources.csv?raw"),
  "belgium_vwo_verified_resources.csv": () => import("@/data/belgium_vwo_verified_resources.csv?raw"),
  "czechia_mo_verified_resources.csv": () => import("@/data/czechia_mo_verified_resources.csv?raw"),
  "malaysia_peninsula_dcs1123_verified_resources.csv": () => import("@/data/malaysia_peninsula_dcs1123_verified_resources.csv?raw"),
  "malaysia_mco_verified_resources.csv": () => import("@/data/malaysia_mco_verified_resources.csv?raw"),
  "malaysia_imonst_verified_resources.csv": () => import("@/data/malaysia_imonst_verified_resources.csv?raw"),
  "malaysia_uitm_mo_verified_resources.csv": () => import("@/data/malaysia_uitm_mo_verified_resources.csv?raw"),
  "malaysia_mcc2025_verified_resources.csv": () => import("@/data/malaysia_mcc2025_verified_resources.csv?raw"),
  "malaysia_emos_imas2025_verified_resources.csv": () => import("@/data/malaysia_emos_imas2025_verified_resources.csv?raw"),
  "malaysia_emos_som2025_verified_resources.csv": () => import("@/data/malaysia_emos_som2025_verified_resources.csv?raw"),
  "malaysia_mco2015_solutions_verified_resources.csv": () => import("@/data/malaysia_mco2015_solutions_verified_resources.csv?raw"),
  "malaysia_mco_codeforces_verified_resources.csv": () => import("@/data/malaysia_mco_codeforces_verified_resources.csv?raw"),
  "malaysia_mco_direct_tasks_verified_resources.csv": () => import("@/data/malaysia_mco_direct_tasks_verified_resources.csv?raw"),
  "malaysia_mco_2024_2025_verified_resources.csv": () => import("@/data/malaysia_mco_2024_2025_verified_resources.csv?raw"),
  "malaysia_mco_2023_verified_resources.csv": () => import("@/data/malaysia_mco_2023_verified_resources.csv?raw"),
  "indonesia_toki_verified_resources.csv": () => import("@/data/indonesia_toki_verified_resources.csv?raw"),
  "indonesia_osn_solutions_verified_resources.csv": () => import("@/data/indonesia_osn_solutions_verified_resources.csv?raw"),
  "indonesia_osn_pdf_verified_resources.csv": () => import("@/data/indonesia_osn_pdf_verified_resources.csv?raw"),
  "indonesia_ioi2022_verified_resources.csv": () => import("@/data/indonesia_ioi2022_verified_resources.csv?raw"),
  "indonesia_binus_icpc2022_verified_resources.csv": () => import("@/data/indonesia_binus_icpc2022_verified_resources.csv?raw"),
  "indonesia_binus_icpc2021_verified_resources.csv": () => import("@/data/indonesia_binus_icpc2021_verified_resources.csv?raw"),
  "indonesia_binus_icpc2020_verified_resources.csv": () => import("@/data/indonesia_binus_icpc2020_verified_resources.csv?raw"),
  "singapore_official_math_verified_resources.csv": () => import("@/data/singapore_official_math_verified_resources.csv?raw"),
  "thailand_timo_verified_resources.csv": () => import("@/data/thailand_timo_verified_resources.csv?raw"),
  "thailand_kku_dm_verified_resources.csv": () => import("@/data/thailand_kku_dm_verified_resources.csv?raw"),
  "thailand_kku_2014_verified_resources.csv": () => import("@/data/thailand_kku_2014_verified_resources.csv?raw"),
  "thailand_muic_verified_resources.csv": () => import("@/data/thailand_muic_verified_resources.csv?raw"),
  "thailand_chula_verified_resources.csv": () => import("@/data/thailand_chula_verified_resources.csv?raw"),
  "thailand_siit_verified_resources.csv": () => import("@/data/thailand_siit_verified_resources.csv?raw"),
  "thailand_kku_2010_assessments_verified_resources.csv": () => import("@/data/thailand_kku_2010_assessments_verified_resources.csv?raw"),
  "thailand_kku_2010_quizzes_verified_resources.csv": () => import("@/data/thailand_kku_2010_quizzes_verified_resources.csv?raw"),
  "thailand_kku_2014_2013_exams_verified_resources.csv": () => import("@/data/thailand_kku_2014_2013_exams_verified_resources.csv?raw"),
  "thailand_kku_2012_homework_verified_resources.csv": () => import("@/data/thailand_kku_2012_homework_verified_resources.csv?raw"),
  "thailand_kku_2011_assessments_verified_resources.csv": () => import("@/data/thailand_kku_2011_assessments_verified_resources.csv?raw"),
  "thailand_kku_2009_homework_verified_resources.csv": () => import("@/data/thailand_kku_2009_homework_verified_resources.csv?raw"),
  "thailand_chula_2007_practice_verified_resources.csv": () => import("@/data/thailand_chula_2007_practice_verified_resources.csv?raw"),
  "thailand_mahidol_muic_math_verified_resources.csv": () => import("@/data/thailand_mahidol_muic_math_verified_resources.csv?raw"),
  "thailand_icpc_bangkok2025_verified_resources.csv": () => import("@/data/thailand_icpc_bangkok2025_verified_resources.csv?raw"),
  "thailand_chula_icpc2024_editorials_verified_resources.csv": () => import("@/data/thailand_chula_icpc2024_editorials_verified_resources.csv?raw"),
  "thailand_kku_discrete_snapshot_verified_resources.csv": () => import("@/data/thailand_kku_discrete_snapshot_verified_resources.csv?raw"),
  "philippines_noiph_pdf_verified_resources.csv": () => import("@/data/philippines_noiph_pdf_verified_resources.csv?raw"),
  "philippines_noiph2020_gym_verified_resources.csv": () => import("@/data/philippines_noiph2020_gym_verified_resources.csv?raw"),
  "philippines_noiph2020_eliminations_verified_resources.csv": () => import("@/data/philippines_noiph2020_eliminations_verified_resources.csv?raw"),
  "sri_lanka_ousl_verified_resources.csv": () => import("@/data/sri_lanka_ousl_verified_resources.csv?raw"),
  "kenya_must_verified_resources.csv": () => import("@/data/kenya_must_verified_resources.csv?raw"),
  "kenya_university_math_verified_resources.csv": () => import("@/data/kenya_university_math_verified_resources.csv?raw"),
  "tanzania_necta_verified_resources.csv": () => import("@/data/tanzania_necta_verified_resources.csv?raw"),
  "uganda_uneb_verified_resources.csv": () => import("@/data/uganda_uneb_verified_resources.csv?raw"),
  "nepal_lec_verified_resources.csv": () => import("@/data/nepal_lec_verified_resources.csv?raw"),
  "nepal_mano_verified_resources.csv": () => import("@/data/nepal_mano_verified_resources.csv?raw"),
  "zimbabwe_buse_verified_resources.csv": () => import("@/data/zimbabwe_buse_verified_resources.csv?raw"),
  "rwanda_nesa_verified_resources.csv": () => import("@/data/rwanda_nesa_verified_resources.csv?raw"),
};

const chunkCache = new Map<string, Promise<CatalogRow[]>>();

export const catalogCountries = Object.keys(catalogCountryIndex).sort((left, right) => left.localeCompare(right));
export const lazyCatalogChunkNames = Object.keys(csvChunkLoaders);

export function lazyChunksForCountries(countries: string[]) {
  return Array.from(new Set(countries.flatMap((country) => lazyChunksByCountry[country] ?? [])));
}

export async function loadCatalogChunks(chunkNames: string[]) {
  const rows = await Promise.all(chunkNames.filter((name) => csvChunkLoaders[name]).map((name) => {
    if (!chunkCache.has(name)) {
      chunkCache.set(name, csvChunkLoaders[name]().then((module) => parseCsv(module.default)));
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
    image: "/manus-storage/ga-signal-illustration_2ca1945f.jpg",
  },
  EM: {
    label: "Engineering Mathematics",
    short: "Calculus, linear algebra, probability, and mathematical methods.",
    color: "teal",
    image: "/manus-storage/em-signal-illustration_df924d6c.jpg",
  },
  DM: {
    label: "Discrete Mathematics",
    short: "Logic, combinatorics, graphs, algorithms, and structures.",
    color: "coral",
    image: "/manus-storage/dm-signal-illustration_d73d2edb.jpg",
  },
  CS: {
    label: "Computer Science",
    short: "Algorithms, data structures, programming, and computational thinking.",
    color: "indigo",
    image: "/manus-storage/dm-signal-illustration_d73d2edb.jpg",
  },
  S: {
    label: "Science",
    short: "Physics, chemistry, biology, and scientific reasoning.",
    color: "sky",
    image: "/manus-storage/em-signal-illustration_df924d6c.jpg",
  },
  T: {
    label: "Technology",
    short: "Practical computing, tooling, and applied digital skills.",
    color: "slate",
    image: "/manus-storage/em-signal-illustration_df924d6c.jpg",
  },
  E: {
    label: "Engineering",
    short: "Design, systems, and applied problem-solving practice.",
    color: "olive",
    image: "/manus-storage/em-signal-illustration_df924d6c.jpg",
  },
  A: {
    label: "Arts",
    short: "Creative, spatial, and design-oriented thinking.",
    color: "rose",
    image: "/manus-storage/ga-signal-illustration_2ca1945f.jpg",
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
