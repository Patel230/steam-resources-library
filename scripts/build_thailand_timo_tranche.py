from __future__ import annotations

import csv
import subprocess
from pathlib import Path


"""Build the narrowly scoped Thailand TIMO sample-paper tranche.

The official TIMO page exposes one direct public sample-paper PDF. This script
does not infer additional records from paid, login, or navigation routes.
"""

ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
OUTPUT = ROOT / "client/src/data/thailand_timo_verified_resources.csv"
AUDIT = ROOT / "research/thailand_timo_url_audit.csv"
SOURCE_URL = "https://www.thaiimo.com/sample-paper.html"
RESOURCE_URL = "https://www.thaiimo.com/uploads/2/8/9/2/28923219/timo_sample_paper.pdf"
VERIFY_DATE = "2026-08-15"

FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
    "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
    "verification_status", "free_resource",
]


def verify(url: str) -> tuple[int, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "30",
            "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    raw = result.stdout.strip()
    if result.returncode != 0 or "|" not in raw:
        return 0, "unavailable"
    code, content_type = raw.split("|", 1)
    return int(code) if code.isdigit() else 0, content_type.lower() or "unknown"


def main() -> None:
    status, content_type = verify(RESOURCE_URL)
    included = status == 200 and "pdf" in content_type

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included"])
        writer.writerow([RESOURCE_URL, status, content_type, "Yes" if included else "No"])

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        if included:
            writer.writerow({
                "country": "Thailand",
                "track": "GA",
                "topic_tags": "mathematical olympiad;problem solving;general aptitude;sample questions",
                "priority": "A",
                "source_type": "Official international olympiad archive",
                "source_title": "Thailand International Mathematical Olympiad (TIMO)",
                "source_url": SOURCE_URL,
                "resource_title": "TIMO — Sample Questions (All Groups)",
                "resource_url": RESOURCE_URL,
                "resource_class": "Official olympiad sample problem paper",
                "language": "English-facing bilingual source",
                "notes": "Public PDF explicitly linked from the official TIMO Sample Paper page. Original paper is bilingual and includes English question text.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    print(f"TIMO direct PDF: HTTP {status} ({content_type})")
    print(f"Wrote {1 if included else 0} verified Thailand TIMO records to {OUTPUT}")


if __name__ == "__main__":
    main()
