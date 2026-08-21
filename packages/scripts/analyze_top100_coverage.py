"""Measure catalog rows per top-100 priority country without inferring verification."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "apps/web/src/data"
ROSTER = ROOT / "research/top100_country_roster.csv"
OUTPUT = ROOT / "research/top100_coverage_baseline.csv"

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


def main() -> None:
    with ROSTER.open(newline="", encoding="utf-8") as handle:
        target = [row["country"] for row in csv.DictReader(handle)]
    target_set = set(target)
    counts = Counter()
    classified_free = Counter()
    for filename in FILES:
        with (DATA / filename).open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                countries = [part.strip() for part in row.get("country", "").split("/")]
                for country in countries:
                    if country not in target_set:
                        continue
                    counts[country] += 1
                    if row.get("free_resource", "").strip().lower() == "yes":
                        classified_free[country] += 1
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "country", "all_current_catalog_rows", "classified_free_rows", "gap_to_100_classified_free"])
        for rank, country in enumerate(target, start=1):
            free_count = classified_free[country]
            writer.writerow([rank, country, counts[country], free_count, max(0, 100 - free_count)])
    below = sum(classified_free[country] < 100 for country in target)
    print(f"Wrote {OUTPUT}")
    print(f"Countries at 100+ classified-free records: {len(target) - below}/100")
    print("Largest classified-free counts:")
    for country, count in classified_free.most_common(15):
        print(f"{country}: {count}")


if __name__ == "__main__":
    main()
