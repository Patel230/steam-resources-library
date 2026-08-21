/* Signal Atlas coverage model: one canonical member-state index, live counts, and honest pending states. */
import { MemberState, UN_MEMBER_STATES } from "@/data/memberStates";
import { REGION_ORDER, Region, regionForState } from "@/data/regions";
import { catalogCountryIndex } from "@/data/catalogIndex";

export type CoverageStatus = "active" | "caveat" | "pending";

export type CoverageEntry = {
  state: MemberState;
  status: CoverageStatus;
  catalogCount: number;
  freeCount: number;
  caveatCount: number;
};

export type RegionCoverageEntry = {
  region: Region;
  total: number;
  active: number;
  caveat: number;
  pending: number;
  freeCount: number;
  catalogCount: number;
};

const stateAliases: Partial<Record<MemberState, string[]>> = {
  Bahamas: ["Bahamas (The)", "The Bahamas"],
  Bolivia: ["Bolivia (Plurinational State of)"],
  Brunei: ["Brunei Darussalam"],
  "Côte d’Ivoire": ["Côte D'Ivoire", "Cote d'Ivoire"],
  China: ["China (the People's Republic of)"],
  Gambia: ["Gambia (Republic of The)"],
  "Guinea-Bissau": ["Guinea Bissau"],
  Iran: ["Iran (Islamic Republic of)"],
  Laos: ["Lao People’s Democratic Republic", "Lao People's Democratic Republic"],
  Micronesia: ["Micronesia (Federated States of)"],
  Myanmar: ["Myanmar (Burma)"],
  Nauru: ["Naoero"],
  "North Korea": ["Democratic People's Republic of Korea"],
  Netherlands: ["Netherlands (Kingdom of the)"],
  Russia: ["Russian Federation"],
  Syria: ["Syrian Arab Republic"],
  Tanzania: ["United Republic of Tanzania"],
  "United Kingdom": ["United Kingdom of Great Britain and Northern Ireland"],
  "United States": ["United States of America"],
  Venezuela: ["Venezuela, Bolivarian Republic of"],
};

function labelsForState(state: MemberState) {
  return new Set([state, ...(stateAliases[state] ?? [])]);
}

export function buildCoverageIndex(): CoverageEntry[] {
  return UN_MEMBER_STATES.map((state) => {
    const totals = Array.from(labelsForState(state)).reduce((summary, label) => {
      const stat = catalogCountryIndex[label];
      if (!stat) return summary;
      return {
        catalogCount: summary.catalogCount + stat.catalogCount,
        freeCount: summary.freeCount + stat.freeCount,
        caveatCount: summary.caveatCount + stat.caveatCount,
      };
    }, { catalogCount: 0, freeCount: 0, caveatCount: 0 });
    return {
      state,
      status: totals.freeCount === 0 ? "pending" : totals.caveatCount > 0 ? "caveat" : "active",
      ...totals,
    };
  });
}

export const coverageIndex = buildCoverageIndex();

export function buildRegionCoverage(): RegionCoverageEntry[] {
  const entries = buildCoverageIndex();
  return REGION_ORDER.map((region) => {
    const regionEntries = entries.filter((entry) => regionForState(entry.state) === region);
    return {
      region,
      total: regionEntries.length,
      active: regionEntries.filter((entry) => entry.status === "active").length,
      caveat: regionEntries.filter((entry) => entry.status === "caveat").length,
      pending: regionEntries.filter((entry) => entry.status === "pending").length,
      freeCount: regionEntries.reduce((sum, entry) => sum + entry.freeCount, 0),
      catalogCount: regionEntries.reduce((sum, entry) => sum + entry.catalogCount, 0),
    };
  });
}

export const regionCoverage = buildRegionCoverage();

export const globalTrackStats = {
  catalogCount: catalogCountryIndex.Global?.catalogCount ?? 0,
  freeCount: catalogCountryIndex.Global?.freeCount ?? 0,
};
