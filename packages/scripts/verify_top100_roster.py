"""Verify and document the World Bank population basis of the top-100 roster."""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from urllib.request import urlopen


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
ROSTER = ROOT / "research/top100_country_roster.csv"
REPORT = ROOT / "research/top100_roster_methodology.md"
INDICATOR = "SP.POP.TOTL"
YEAR = 2024
API_URL = f"https://api.worldbank.org/v2/country/all/indicator/{INDICATOR}?date={YEAR}&format=json&per_page=400"
INDICATOR_URL = "https://data.worldbank.org/indicator/SP.POP.TOTL"
METADATA_URL = "https://databank.worldbank.org/metadataglossary/gender-statistics/series/SP.POP.TOTL"


def fetch_world_bank_values() -> dict[str, int]:
    with urlopen(API_URL, timeout=30) as response:  # nosec B310: fixed HTTPS World Bank endpoint
        payload = json.load(response)
    values: dict[str, int] = {}
    for row in payload[1]:
        if row.get("value") is not None:
            values[row["country"]["value"]] = int(row["value"])
    return values


def main() -> None:
    with ROSTER.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    world_bank = fetch_world_bank_values()

    issues: list[str] = []
    if len(rows) != 100:
        issues.append(f"Roster has {len(rows)} rows rather than 100.")
    if [int(row["rank"]) for row in rows] != list(range(1, len(rows) + 1)):
        issues.append("Ranks are not a contiguous 1..100 sequence.")
    if len({row["country"] for row in rows}) != len(rows):
        issues.append("Roster includes duplicate canonical country names.")

    populations = [int(row["population_2024"]) for row in rows]
    if populations != sorted(populations, reverse=True):
        issues.append("Population values are not in descending order.")

    mismatches: list[str] = []
    for row in rows:
        source_label = row["world_bank_country_label"]
        expected = int(row["population_2024"])
        actual = world_bank.get(source_label)
        if actual is None:
            mismatches.append(f"{row['country']}: World Bank label '{source_label}' absent from API response")
        elif actual != expected:
            mismatches.append(f"{row['country']}: roster={expected:,}, World Bank={actual:,}")
    if mismatches:
        issues.append(f"{len(mismatches)} World Bank value mismatch(es).")

    today = date.today().isoformat()
    lines = [
        "# Top-100 country prioritization methodology",
        "",
        "## Ranking basis",
        "",
        "Signal Atlas prioritizes the **100 most populous UN member states** using the World Bank World Development Indicators **Population, total** series (`SP.POP.TOTL`) for **2024**. The roster retains a canonical site-facing country name, the 2024 numeric value, and the World Bank country label used for source reconciliation.",
        "",
        "> The World Bank defines `SP.POP.TOTL` as total population under the *de facto* definition—counting all residents regardless of legal status or citizenship—and reports mid-year estimates. The indicator is annual. [World Bank metadata](" + METADATA_URL + ")",
        "",
        f"The published indicator page lists 2024 among the available reference years and identifies the underlying population sources. [Indicator page]({INDICATOR_URL})",
        "",
        "## Reproducible verification",
        "",
        f"On **{today}**, `scripts/verify_top100_roster.py` retrieved the official World Bank API for [2024 `SP.POP.TOTL`]({API_URL}) and checked the local `top100_country_roster.csv` for a 100-row contiguous rank sequence, unique country names, descending population values, and exact numeric agreement for every World Bank label.",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| Roster rows | {len(rows)} |",
        f"| Rank sequence | {'PASS' if [int(row['rank']) for row in rows] == list(range(1, len(rows) + 1)) else 'FAIL'} |",
        f"| Unique country names | {'PASS' if len({row['country'] for row in rows}) == len(rows) else 'FAIL'} |",
        f"| Descending 2024 population order | {'PASS' if populations == sorted(populations, reverse=True) else 'FAIL'} |",
        f"| World Bank numeric reconciliation | {'PASS — 100/100' if not mismatches else f'FAIL — {len(mismatches)} mismatch(es)'} |",
        "",
        "The ranking is a research-prioritization device, not a claim that resource availability is proportional to population. The coverage directory continues to display verified free-resource counts and shortfalls rather than inferring completeness from rank.",
    ]
    if mismatches:
        lines.extend(["", "## Reconciliation exceptions", ""] + [f"- {item}" for item in mismatches])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {REPORT}")
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        raise SystemExit(1)
    print("PASS: 100/100 World Bank 2024 values reconcile; ranks are contiguous, unique, and descending.")


if __name__ == "__main__":
    main()
