"""Build the official NOI.PH 2020 Online Eliminations public archive tranche.

The first-party NOI.PH Eliminations post identifies the 17-problem online round
and directly publishes the Codeforces contest URL. Browser checks confirm that
the public NOI.PH group contest exposes an English task list and substantive
English task statements without login. This writes one bounded archive record,
not 17 inferred task records.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "philippines_noiph2020_eliminations_verified_resources.csv"
AUDIT = ROOT / "research/philippines_noiph2020_eliminations_url_audit.csv"
SOURCE_URL = "https://noi.ph/2020-national-eliminations/"
RESOURCE_URL = "https://codeforces.com/group/Sw3sdIlMPV/contest/266012"
VERIFY_DATE = "2026-08-15"


def catalog_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle))
    return urls


def main() -> None:
    existing = catalog_urls()
    if RESOURCE_URL in existing:
        raise RuntimeError(f"Duplicate live resource URL: {RESOURCE_URL}")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    row = {
        "country": "Philippines",
        "track": "DM",
        "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;contest;olympiad",
        "priority": "A",
        "source_type": "National programming Olympiad official contest archive",
        "source_title": "NOI.PH 2020 National Eliminations official contest post",
        "source_url": SOURCE_URL,
        "resource_title": "NOI.PH 2020 National Eliminations — public English 17-problem archive",
        "resource_url": RESOURCE_URL,
        "resource_class": "National programming Olympiad contest problem archive",
        "language": "English",
        "notes": "The official NOI.PH post directly links this public Codeforces contest and states that the online eliminations comprised 17 problems. Unauthenticated browser verification found the NOI.PH public group, English task list, and a substantive English task statement with input, output, scoring, and examples. Login is required only to submit practice solutions, not to view the archive.",
        "access_model": "Free public web archive",
        "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
        "free_resource": "Yes",
    }
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "source_url", "resource_url", "source_post_direct_link", "browser_http_status", "organiser_owned_source",
            "no_login_archive_view", "english_task_list", "substantive_statement_checked", "visible_task_count", "included", "verification_note",
        ])
        writer.writeheader()
        writer.writerow({
            "source_url": SOURCE_URL,
            "resource_url": RESOURCE_URL,
            "source_post_direct_link": "Yes",
            "browser_http_status": "200",
            "organiser_owned_source": "Yes",
            "no_login_archive_view": "Yes",
            "english_task_list": "Yes",
            "substantive_statement_checked": "Yes — Problem A: input, output, scoring, examples",
            "visible_task_count": "17",
            "included": "Yes",
            "verification_note": "Official NOI.PH post says the round was held online on Codeforces, consisted of 17 problems, and that problems remain accessible for practice. Browser showed public NOI.PH group/contest and a rendered English statement without authentication.",
        })

    print(f"Wrote 1 verified official NOI.PH 2020 Online Eliminations archive record to {OUTPUT}")


if __name__ == "__main__":
    main()
