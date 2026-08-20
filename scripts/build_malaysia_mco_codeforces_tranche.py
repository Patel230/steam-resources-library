from __future__ import annotations

import csv
from pathlib import Path


"""Build the browser-verified public MIPS / IOI Malaysia Codeforces tranche.

Codeforces returns anti-bot HTTP 403 to sandbox curl even when the same page is
available to an unauthenticated web browser. This generator preserves the
separate browser verification evidence rather than misclassifying those public
archives as unavailable. Each row below was browser-checked on 2026-08-15 for
HTTP 200, public IOI Malaysia group context, English task cues, and visible task
links. The official MIPS practice archive links the annual MCO contests, and the
same public organiser-owned group lists the camp archives.
"""

ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "malaysia_mco_codeforces_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_mco_codeforces_url_audit.csv"
SOURCE_URL = "https://ioimalaysia.org/resource/for-student/practice/"
VERIFY_DATE = "2026-08-15"

# title, contest URL, resource class, visible English task count in the
# unauthenticated browser audit. Two candidates that returned browser HTTP 503
# (Camp 2026 Day 5 Elementary and Day 6 Advanced) are deliberately omitted.
BROWSER_VERIFIED = [
    ("MCO 2020", "https://codeforces.com/group/IO0c6wbyI8/contest/293254", "Official MCO contest task archive", 5),
    ("MCO 2021", "https://codeforces.com/group/IO0c6wbyI8/contest/325025", "Official MCO contest task archive", 5),
    ("MCO 2022", "https://codeforces.com/group/IO0c6wbyI8/contest/375943", "Official MCO contest task archive", 5),
    ("MCO 2023", "https://codeforces.com/group/IO0c6wbyI8/contest/431909", "Official MCO contest task archive", 4),
    ("MCO 2024", "https://codeforces.com/group/IO0c6wbyI8/contest/105087", "Official MCO contest task archive", 4),
    ("MCO 2025", "https://codeforces.com/group/IO0c6wbyI8/contest/606535", "Official MCO contest task archive", 4),
    ("MCO 2026", "https://codeforces.com/group/IO0c6wbyI8/contest/106510", "Official MCO contest task archive", 4),
    ("MCO 2023 Training Camp Day 2", "https://codeforces.com/group/IO0c6wbyI8/contest/415527", "Official MCO training-camp task archive", 10),
    ("MCO 2023 Training Camp Day 3", "https://codeforces.com/group/IO0c6wbyI8/contest/415614", "Official MCO training-camp task archive", 7),
    ("MCO 2024 Training Camp Day 1", "https://codeforces.com/group/IO0c6wbyI8/contest/493595", "Official MCO training-camp task archive", 5),
    ("MCO 2024 Training Camp Day 2", "https://codeforces.com/group/IO0c6wbyI8/contest/493780", "Official MCO training-camp task archive", 5),
    ("MCO 2024 Training Camp Day 3", "https://codeforces.com/group/IO0c6wbyI8/contest/493867", "Official MCO training-camp task archive", 7),
    ("MCO Camp 2026 Day 2 Advanced", "https://codeforces.com/group/IO0c6wbyI8/contest/658994", "Official MCO training-camp task archive", 8),
    ("MCO Camp 2026 Day 2 Elementary", "https://codeforces.com/group/IO0c6wbyI8/contest/658912", "Official MCO training-camp task archive", 8),
    ("MCO Camp 2026 Day 3 Elementary", "https://codeforces.com/group/IO0c6wbyI8/contest/659055", "Official MCO training-camp task archive", 9),
    ("MCO Camp 2026 Day 4 Advanced", "https://codeforces.com/group/IO0c6wbyI8/contest/660578", "Official MCO training-camp task archive", 6),
    ("MCO Camp 2026 Day 4 Elementary", "https://codeforces.com/group/IO0c6wbyI8/contest/660449", "Official MCO training-camp task archive", 8),
    ("MCO Camp 2026 Day 5 Advanced", "https://codeforces.com/group/IO0c6wbyI8/contest/661513", "Official MCO training-camp task archive", 8),
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
    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for title, resource_url, resource_class, task_count in rows:
            writer.writerow({
                "country": "Malaysia",
                "track": "DM",
                "topic_tags": "algorithms;competitive programming;discrete mathematics;informatics;contest",
                "priority": "A",
                "source_type": "Official national computing olympiad archive",
                "source_title": "Malaysian Informatics and Programming Society (MIPS) — MCO archive",
                "source_url": SOURCE_URL,
                "resource_title": f"{title} — public English task archive",
                "resource_url": resource_url,
                "resource_class": resource_class,
                "language": "English",
                "notes": f"Official MIPS-linked public IOI Malaysia group archive with {task_count} visible English task link(s); browser HTTP 200 verification retained because direct curl receives an anti-bot 403.",
                "access_model": "Free public web archive",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "title", "browser_http_status", "ioi_malaysia_public_group", "english_task_links", "visible_task_count", "included", "verification_note"])
        for title, resource_url, _resource_class, task_count in BROWSER_VERIFIED:
            writer.writerow([resource_url, title, 200, "Yes", "Yes", task_count, "Yes", "Unauthenticated browser verification; sandbox curl receives Codeforces anti-bot 403."])
        writer.writerow(["https://codeforces.com/group/IO0c6wbyI8/contest/661533", "MCO Camp 2026 Day 5 Elementary", 503, "No", "No", 0, "No", "Public browser audit returned HTTP 503; excluded."])
        writer.writerow(["https://codeforces.com/group/IO0c6wbyI8/contest/661885", "MCO Camp 2026 Day 6 Advanced", 503, "No", "No", 0, "No", "Public browser audit returned HTTP 503; excluded."])
    print(f"Wrote {len(rows)} verified MCO records to {OUTPUT}")


if __name__ == "__main__":
    main()
