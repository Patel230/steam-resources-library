"""Build a reproducible top-100 research roster from World Bank population data.

The catalog continues to use the canonical UN member-state names in apps/web/src/data/memberStates.ts.
This helper maps World Bank display names to those canonical labels, excludes non-members, and
writes a research-facing roster without modifying catalog data.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from urllib.request import urlopen


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
MEMBERS_PATH = ROOT / "apps/web/src/data/memberStates.ts"
OUTPUT_CSV = ROOT / "research/top100_country_roster.csv"
OUTPUT_MD = ROOT / "research/top100_country_roster.md"
WORLD_BANK_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL"
    "?date=2024&format=json&per_page=400"
)

ALIASES = {
    "Bahamas, The": "Bahamas",
    "Bolivia": "Bolivia",
    "Brunei Darussalam": "Brunei",
    "Congo, Dem. Rep.": "Democratic Republic of the Congo",
    "Congo, Rep.": "Congo",
    "Cote d'Ivoire": "Côte d’Ivoire",
    "Egypt, Arab Rep.": "Egypt",
    "Gambia, The": "Gambia",
    "Iran, Islamic Rep.": "Iran",
    "Korea, Dem. People's Rep.": "North Korea",
    "Korea, Rep.": "Republic of Korea",
    "Kyrgyz Republic": "Kyrgyzstan",
    "Lao PDR": "Laos",
    "Micronesia, Fed. Sts.": "Micronesia",
    "Moldova": "Republic of Moldova",
    "Slovak Republic": "Slovakia",
    "St. Kitts and Nevis": "Saint Kitts and Nevis",
    "St. Lucia": "Saint Lucia",
    "St. Vincent and the Grenadines": "Saint Vincent and the Grenadines",
    "Syrian Arab Republic": "Syria",
    "Turkiye": "Türkiye",
    "Venezuela, RB": "Venezuela",
    "Vietnam": "Viet Nam",
    "Yemen, Rep.": "Yemen",
}


def canonical_members() -> set[str]:
    content = MEMBERS_PATH.read_text(encoding="utf-8")
    match = re.search(r"UN_MEMBER_STATES\s*=\s*\[(.*?)\]\s+as const", content, re.S)
    if not match:
        raise ValueError("Could not locate UN_MEMBER_STATES in memberStates.ts")
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def main() -> None:
    members = canonical_members()
    with urlopen(WORLD_BANK_URL, timeout=30) as response:
        payload = json.load(response)
    rows = []
    for record in payload[1]:
        canonical = ALIASES.get(record["country"]["value"], record["country"]["value"])
        population = record.get("value")
        if canonical in members and isinstance(population, (int, float)):
            rows.append((canonical, int(population), record["country"]["value"]))
    rows.sort(key=lambda item: item[1], reverse=True)
    top_100 = rows[:100]
    if len(top_100) != 100:
        raise ValueError(f"Expected 100 member states, found {len(top_100)}")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "country", "population_2024", "world_bank_country_label"])
        for rank, (country, population, source_name) in enumerate(top_100, start=1):
            writer.writerow([rank, country, population, source_name])

    lines = [
        "# Top-100 country research roster",
        "",
        "**Priority basis:** latest available World Bank total-population indicator (SP.POP.TOTL) for 2024, filtered to Signal Atlas’s canonical list of 193 UN member states. This is a research-priority roster, not a quality ranking of countries or education systems.",
        "",
        "The underlying UN World Population Prospects 2024 release presents official estimates and projections for 237 countries or areas; the World Bank indicator provides a readily queryable country-level ranking aligned to the same population-priority purpose.",
        "",
        "| Rank | Canonical Signal Atlas country | 2024 population | World Bank label |",
        "| ---: | --- | ---: | --- |",
    ]
    for rank, (country, population, source_name) in enumerate(top_100, start=1):
        lines.append(f"| {rank} | {country} | {population:,} | {source_name} |")
    lines.extend([
        "",
        "## Research target",
        "",
        "Each listed country is targeted for at least 100 **unique, free, publicly accessible, provenance-recorded** GA, EM, or DM resources. A country may remain below the target when first-party and reputable public sources do not support an honest 100-resource collection; shortfalls must remain visible rather than be filled with fabricated or repeated records.",
        "",
        "## Sources",
        "",
        "1. United Nations, World Population Prospects 2024: https://www.un.org/development/desa/pd/content/world-population-prospects-2024-dataset",
        "2. World Bank, Population, total (SP.POP.TOTL): https://data.worldbank.org/indicator/SP.POP.TOTL",
        "",
    ])
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(top_100)} countries to {OUTPUT_CSV} and {OUTPUT_MD}")
    print("Top 10:", ", ".join(country for country, _, _ in top_100[:10]))
    print("100th:", top_100[-1][0])


if __name__ == "__main__":
    main()
