"""Summarize legacy source concentrations for one canonical country label."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path


DATA = Path("/home/ubuntu/ga-em-dm-resource-hub/apps/web/src/data/final_resources.csv")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/summarize_legacy_country.py 'India'")
    country = sys.argv[1]
    rows = []
    with DATA.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if country in [part.strip() for part in row.get("country", "").split("/")]:
                rows.append(row)
    sources = Counter((row["source_title"], row["source_url"]) for row in rows)
    print(f"{country}: {len(rows)} legacy rows")
    for (title, url), count in sources.most_common(40):
        print(f"{count:4d}\t{title}\t{url}")


if __name__ == "__main__":
    main()
