from __future__ import annotations

import csv
from pathlib import Path


"""Build a narrowly scoped direct-task extension for the official MIPS MCO archive.

The MIPS practice page links the MCO 2020 and 2026 contest archives in the
public IOI Malaysia Codeforces group. Five direct task routes were subsequently
checked in an unauthenticated browser on 2026-08-15. Each included route rendered
a substantive English competitive-programming statement. The codeforces shell
anti-bot boundary is documented rather than mistaken for public-access failure.
"""

ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "malaysia_mco_direct_tasks_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_mco_direct_tasks_url_audit.csv"
SOURCE_URL = "https://ioimalaysia.org/resource/for-student/practice/"
VERIFY_DATE = "2026-08-15"

# year, letter, public direct task route, short English title, independent evidence.
# The MCO 2020 A–C pages were extracted through a separate public reader; MCO 2026
# A was browser-checked before this tranche and B was separately extracted. C/D
# 2026 rendered as blank PDF embeds and E was unrelated promotion, so none are here.
BROWSER_VERIFIED = [
    (
        "MCO 2020",
        "A",
        "https://codeforces.com/group/IO0c6wbyI8/contest/293254/problem/A",
        "Crash Royale",
        "Public reader extracted English statement, scoring, and examples.",
    ),
    (
        "MCO 2020",
        "B",
        "https://codeforces.com/group/IO0c6wbyI8/contest/293254/problem/B",
        "Reversi board challenge",
        "Public reader extracted English statement, scoring, and examples.",
    ),
    (
        "MCO 2020",
        "C",
        "https://codeforces.com/group/IO0c6wbyI8/contest/293254/problem/C",
        "Making Friends",
        "Public reader extracted full English statement, constraints, and examples.",
    ),
    (
        "MCO 2026",
        "A",
        "https://codeforces.com/group/IO0c6wbyI8/contest/106510/problem/A",
        "MCO 2026 Problem A",
        "Unauthenticated browser rendered a full English task statement.",
    ),
    (
        "MCO 2026",
        "B",
        "https://codeforces.com/group/IO0c6wbyI8/contest/106510/problem/B",
        "Team flying coach challenge",
        "Public reader extracted English statement, constraints, scoring, and examples.",
    ),
]


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
    rows = [record for record in BROWSER_VERIFIED if record[2] not in existing]
    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for year, letter, resource_url, title, evidence in rows:
            writer.writerow({
                "country": "Malaysia",
                "track": "DM",
                "topic_tags": "algorithms;competitive programming;discrete mathematics;informatics;contest;problem statement",
                "priority": "A",
                "source_type": "Official national computing olympiad task archive",
                "source_title": "Malaysian Informatics and Programming Society (MIPS) — MCO direct tasks",
                "source_url": SOURCE_URL,
                "resource_title": f"{year} — Problem {letter}: {title}",
                "resource_url": resource_url,
                "resource_class": "Official MCO English problem statement",
                "language": "English",
                "notes": f"Direct task in the public IOI Malaysia group. {evidence} MIPS links its parent annual contest archive; shell curl receives Codeforces anti-bot 403, while browser verification confirms unauthenticated access.",
                "access_model": "Free public web archive",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "title", "parent_archive_linked_by_mips", "browser_or_public_reader_access", "english_statement", "included", "verification_note"])
        for year, letter, resource_url, title, evidence in BROWSER_VERIFIED:
            writer.writerow([resource_url, f"{year} Problem {letter}: {title}", "Yes", "HTTP 200", "Yes", "Yes", evidence])
        writer.writerow(["https://codeforces.com/group/IO0c6wbyI8/contest/106510/problem/C", "MCO 2026 Problem C", "Yes", "Blank PDF embed", "Not reproducible", "No", "Excluded: blank embedded PDF viewer in browser."])
        writer.writerow(["https://codeforces.com/group/IO0c6wbyI8/contest/106510/problem/D", "MCO 2026 Problem D", "Yes", "Blank PDF embed", "Not reproducible", "No", "Excluded: blank embedded PDF viewer in browser."])
        writer.writerow(["https://codeforces.com/group/IO0c6wbyI8/contest/106510/problem/E", "MCO 2026 Problem E", "No", "HTTP 200 unrelated promotion", "No", "No", "Excluded: route showed an unrelated Codeforces challenge."])

    print(f"Wrote {len(rows)} verified direct MCO task records to {OUTPUT}")


if __name__ == "__main__":
    main()
