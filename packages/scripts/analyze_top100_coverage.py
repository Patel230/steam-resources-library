"""Measure catalog rows per top-100 priority country without inferring verification.

Auto-discovers every CSV chunk in apps/web/src/data and deduplicates by
resource_url so per-country totals reflect unique records. The roster must be
generated first by scripts/build_top100_roster.py.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "apps/web/src/data"
ROSTER = ROOT / "research/top100_country_roster.csv"
OUTPUT = ROOT / "research/top100_coverage_baseline.csv"


def main() -> None:
    with ROSTER.open(newline="", encoding="utf-8") as handle:
        target = [row["country"] for row in csv.DictReader(handle)]
    target_set = set(target)

    counts = Counter()
    classified_free = Counter()
    seen_urls: set[str] = set()

    for path in sorted(DATA.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = (row.get("resource_url") or "").strip()
                if url:
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                countries = [part.strip() for part in row.get("country", "").split("/")]
                for country in countries:
                    if country not in target_set:
                        continue
                    counts[country] += 1
                    if row.get("free_resource", "").strip().lower() == "yes":
                        classified_free[country] += 1

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "country", "all_catalog_rows", "classified_free_rows", "gap_to_100_classified_free"])
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
