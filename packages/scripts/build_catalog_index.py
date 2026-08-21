"""Generate the lightweight client-side index used for catalog discovery and lazy chunk selection."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "apps/web/src/data"
OUTPUT = ROOT / "apps/web/src/data/catalogIndex.ts"

FILES = [
    "free_resources.csv",
    "important_country_resources.csv",
    "european_wave_resources.csv",
    "next_european_wave_resources.csv",
    "south_southeast_asia_resources.csv",
    "active_country_depth_resources.csv",
    "archive_depth_resources.csv",
    "four_country_depth_resources.csv",
    "india_gate_verified_resources.csv",
    "india_tifr_verified_resources.csv",
    "canada_cemc_verified_resources.csv",
    "germany_bwinf_verified_resources.csv",
    "france_ccinp_verified_resources.csv",
    "japan_joi_verified_resources.csv",
    "united_kingdom_bmo_verified_resources.csv",
    "south_africa_computer_olympiad_verified_resources.csv",
    "south_africa_foundation_math_verified_resources.csv",
    "south_africa_junior_math_verified_resources.csv",
    "south_africa_uj_math_verified_resources.csv",
    "south_africa_uj_math_followup_verified_resources.csv",
    "south_africa_uct_2018_verified_resources.csv",
    "south_africa_upmc_verified_resources.csv",
    "south_africa_wits_verified_resources.csv",
    "south_africa_samf_verified_resources.csv",
    "nigeria_waec_verified_resources.csv",
    "new_zealand_nzqa_verified_resources.csv",
    "united_states_usaco_verified_resources.csv",
    "united_states_usaco_2026_verified_resources.csv",
    "brazil_obm_verified_resources.csv",
    "italy_math_olympiad_verified_resources.csv",
    "netherlands_math_olympiad_verified_resources.csv",
    "austria_oemo_verified_resources.csv",
    "australia_scsa_verified_resources.csv",
    "australia_scsa_2022_2025_verified_resources.csv",
    "australia_nesa_2020_2023_verified_resources.csv",
    "australia_nesa_2016_2019_verified_resources.csv",
    "australia_nesa_2015_verified_resources.csv",
    "australia_nesa_2014_mg_verified_resources.csv",
    "australia_nesa_2015_ext_verified_resources.csv",
    "australia_amt_verified_resources.csv",
    "australia_amt_enrichment_verified_resources.csv",
    "australia_qcaa_2025_verified_resources.csv",
    "australia_qcaa_2023_2025_verified_resources.csv",
    "australia_vcaa_2023_2025_verified_resources.csv",
    "australia_vcaa_guides_verified_resources.csv",
    "republic_of_korea_kice_csat_verified_resources.csv",
    "china_ccf_gesp_verified_resources.csv",
    "mexico_omm_canguro_verified_resources.csv",
    "pakistan_pu_verified_resources.csv",
    "pakistan_iba_verified_resources.csv",
    "pakistan_university_followup_verified_resources.csv",
    "pakistan_giki_verified_resources.csv",
    "pakistan_gcu_verified_resources.csv",
    "turkiye_tubitak_verified_resources.csv",
    "russia_fipi_advanced_math_verified_resources.csv",
    "poland_om_verified_resources.csv",
    "belgium_vwo_verified_resources.csv",
    "czechia_mo_verified_resources.csv",
    "malaysia_mco_verified_resources.csv",
    "malaysia_imonst_verified_resources.csv",
    "malaysia_uitm_mo_verified_resources.csv",
    "malaysia_mcc2025_verified_resources.csv",
    "malaysia_emos_imas2025_verified_resources.csv",
    "malaysia_emos_som2025_verified_resources.csv",
    "malaysia_mco2015_solutions_verified_resources.csv",
    "malaysia_mco_codeforces_verified_resources.csv",
    "malaysia_mco_direct_tasks_verified_resources.csv",
    "malaysia_mco_2024_2025_verified_resources.csv",
    "malaysia_mco_2023_verified_resources.csv",
    "indonesia_toki_verified_resources.csv",
    "indonesia_osn_solutions_verified_resources.csv",
    "indonesia_osn_pdf_verified_resources.csv",
    "indonesia_ioi2022_verified_resources.csv",
    "indonesia_binus_icpc2022_verified_resources.csv",
    "indonesia_binus_icpc2021_verified_resources.csv",
    "indonesia_binus_icpc2020_verified_resources.csv",
    "thailand_timo_verified_resources.csv",
    "thailand_kku_dm_verified_resources.csv",
    "thailand_kku_2014_verified_resources.csv",
    "thailand_muic_verified_resources.csv",
    "thailand_chula_verified_resources.csv",
    "thailand_siit_verified_resources.csv",
    "thailand_kku_2010_assessments_verified_resources.csv",
    "thailand_kku_2014_2013_exams_verified_resources.csv",
    "thailand_kku_2012_homework_verified_resources.csv",
    "thailand_kku_2011_assessments_verified_resources.csv",
    "thailand_kku_2009_homework_verified_resources.csv",
    "thailand_chula_2007_practice_verified_resources.csv",
    "thailand_mahidol_muic_math_verified_resources.csv",
    "thailand_icpc_bangkok2025_verified_resources.csv",
    "thailand_chula_icpc2024_editorials_verified_resources.csv",
    "thailand_kku_discrete_snapshot_verified_resources.csv",
    "philippines_noiph_pdf_verified_resources.csv",
    "philippines_noiph2020_gym_verified_resources.csv",
    "philippines_noiph2020_eliminations_verified_resources.csv",
    "kenya_university_math_verified_resources.csv",
    "tanzania_necta_verified_resources.csv",
    "uganda_uneb_verified_resources.csv",
    "nepal_mano_verified_resources.csv",
    "rwanda_nesa_verified_resources.csv",
]

# Keep the historical allowlist for deterministic ordering, but automatically
# include every newly created verified chunk so integrations cannot be omitted
# from the live lazy loader and country totals.
FILES = sorted(set(FILES) | {path.name for path in DATA.glob("*_verified_resources.csv")})

INITIAL_FILES = {
    "free_resources.csv",
    "important_country_resources.csv",
    "european_wave_resources.csv",
    "next_european_wave_resources.csv",
    "south_southeast_asia_resources.csv",
}


def main() -> None:
    rows_by_url: dict[str, dict[str, str]] = {}
    countries_by_url: dict[str, set[str]] = defaultdict(set)
    chunks_by_country: dict[str, set[str]] = defaultdict(set)

    for filename in FILES:
        with (DATA / filename).open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip().lower()
                if not url:
                    continue
                rows_by_url[url] = row
                countries = [country.strip() for country in row.get("country", "").split("/") if country.strip()]
                countries_by_url[url].update(countries)
                for country in countries:
                    if filename not in INITIAL_FILES:
                        chunks_by_country[country].add(filename)

    countries: dict[str, dict[str, int]] = {}
    source_titles: set[str] = set()
    track_counts: Counter[str] = Counter()
    gateway_count = 0
    for url, row in rows_by_url.items():
        source_titles.add(row.get("source_title", ""))
        gateway_count += row.get("resource_class", "") == "Official gateway"
        for track in row.get("track", "").replace(",", " ").replace("/", " ").split():
            if track in {"GA", "EM", "DM"}:
                track_counts[track] += 1
        for country in countries_by_url[url]:
            stat = countries.setdefault(country, {"catalogCount": 0, "freeCount": 0, "caveatCount": 0})
            stat["catalogCount"] += 1
            if row.get("free_resource", "").strip().lower() == "yes":
                stat["freeCount"] += 1
                if "access caveat" in row.get("verification_status", "").lower():
                    stat["caveatCount"] += 1

    country_chunks = {country: sorted(files) for country, files in sorted(chunks_by_country.items())}
    payload = """/* Signal Atlas data index: generated by scripts/build_catalog_index.py. Keep resource rows in lazy CSV chunks. */\n\n"""
    payload += "export type CountryCatalogStat = { catalogCount: number; freeCount: number; caveatCount: number };\n\n"
    payload += f"export const catalogCountryIndex: Record<string, CountryCatalogStat> = {json.dumps(countries, ensure_ascii=False, indent=2)};\n\n"
    payload += f"export const lazyChunksByCountry: Record<string, string[]> = {json.dumps(country_chunks, ensure_ascii=False, indent=2)};\n\n"
    payload += "export const catalogIndexTotals = " + json.dumps({
        "catalogCount": len(rows_by_url),
        "freeCount": sum(1 for row in rows_by_url.values() if row.get("free_resource", "").strip().lower() == "yes"),
        "sourceCount": len(source_titles - {""}),
        "gatewayCount": gateway_count,
        "trackCounts": {track: track_counts[track] for track in ("GA", "EM", "DM")},
    }, indent=2) + " as const;\n"
    OUTPUT.write_text(payload, encoding="utf-8")
    print(f"Wrote {OUTPUT} for {len(rows_by_url)} unique resource URLs across {len(countries)} catalog labels.")


if __name__ == "__main__":
    main()
