"""Build the browser-verified public NOI.PH 2020 Finals Gym archive tranche.

The official NOI.PH National Finals post names its two five-problem rounds and
links directly to the Day 1 and Day 2 Codeforces Gym archives. Codeforces
returns anti-bot responses to some sandbox non-browser requests, so this
generator intentionally preserves individual unauthenticated browser evidence
rather than treating the delivery-layer response as an access restriction.
Only the two visibly public contest archives are emitted; no per-task records
are inferred from the common archive pages.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "philippines_noiph2020_gym_verified_resources.csv"
AUDIT = ROOT / "research/philippines_noiph2020_gym_url_audit.csv"
SOURCE_URL = "https://noi.ph/2020-national-finals/"
VERIFY_DATE = "2026-08-15"

# Each archive was browser-checked without authentication. The official NOI.PH
# post directly links these Gym mirrors, which identify noi.ph as contest site.
BROWSER_VERIFIED = [
    (
        "Day 1",
        "https://codeforces.com/gym/102687",
        5,
        "Hey Gamers; Racoon Virus; Forklifter; Kapuluan ng Kalayaan 2; Crazy Rich Sean",
    ),
    (
        "Day 2",
        "https://codeforces.com/gym/102688",
        5,
        "Functional Alchemy; Ding Ding's Art/Science Exhibit; Lito Lapida and the Copabanana; Drop the Beat; The Darkest Timeline",
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
    rows = [record for record in BROWSER_VERIFIED if record[1] not in existing]
    if not rows:
        raise RuntimeError("No non-duplicate official NOI.PH 2020 Gym archives available to write")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for day, resource_url, task_count, task_names in rows:
            writer.writerow({
                "country": "Philippines",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;contest;olympiad",
                "priority": "A",
                "source_type": "National programming Olympiad organiser-linked contest archive",
                "source_title": "NOI.PH 2020 National Finals official organiser-linked Gym archive",
                "source_url": SOURCE_URL,
                "resource_title": f"NOI.PH 2020 National Finals — {day} public English problem archive",
                "resource_url": resource_url,
                "resource_class": "National programming Olympiad contest problem archive",
                "language": "English",
                "notes": f"The official NOI.PH National Finals post links this public five-task Gym mirror. Browser HTTP 200 verification found the NOI.PH contest identity, English task listing, standard input/output, and {task_count} public task statements ({task_names}). Login is required only to submit practice solutions, not to view the archive.",
                "access_model": "Free public web archive",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "source_url", "resource_url", "resource_title", "browser_http_status", "organiser_linked",
            "no_login_view", "english_visible_tasks", "visible_task_count", "included", "verification_note",
        ])
        for day, resource_url, task_count, task_names in BROWSER_VERIFIED:
            writer.writerow([
                SOURCE_URL,
                resource_url,
                f"NOI.PH 2020 National Finals — {day}",
                200,
                "Yes",
                "Yes",
                "Yes",
                task_count,
                "Yes" if resource_url in {row[1] for row in rows} else "No",
                f"Unauthenticated browser verification; official NOI.PH post links this Gym archive. Visible tasks: {task_names}.",
            ])

    print(f"Wrote {len(rows)} verified official NOI.PH 2020 Gym archive records to {OUTPUT}")


if __name__ == "__main__":
    main()
