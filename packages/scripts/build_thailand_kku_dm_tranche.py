from __future__ import annotations

import csv
import subprocess
from pathlib import Path


"""Build the Khon Kaen University public course-archive tranche.

The material list is taken only from the English 188200 course index. Each
candidate has an item-level HTTP and PDF-content-type test; a failed endpoint
is left in the audit report but is never written to the live catalogue.
"""

ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
OUTPUT = ROOT / "apps/web/src/data/thailand_kku_dm_verified_resources.csv"
AUDIT = ROOT / "research/thailand_kku_dm_url_audit.csv"
SOURCE_URL = "https://gear.kku.ac.th/~polpinit/classes/188200_2013_1/index.html"
BASE_URL = "https://gear.kku.ac.th/~polpinit/classes/188200_2013_1/"
VERIFY_DATE = "2026-08-15"

FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
    "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
    "verification_status", "free_resource",
]

ASSESSMENTS = [
    ("Final examination, 2009", "Exams/Final_2009_1.pdf", "University final examination"),
    ("Final examination, 2010", "Exams/Final_2010_1.pdf", "University final examination"),
    ("Final examination, 2011", "Exams/Final_2011_1.pdf", "University final examination"),
    ("Final examination, 2012", "Exams/Final_2012_1.pdf", "University final examination"),
    ("Midterm examination, 2009", "Exams/Midterm_2009_1.pdf", "University midterm examination"),
    ("Midterm examination, 2010", "Exams/Midterm_2010_1.pdf", "University midterm examination"),
    ("Midterm examination, 2011", "Exams/Midterm_2011_1.pdf", "University midterm examination"),
    ("Midterm examination, 2012", "Exams/Midterm_2012_1.pdf", "University midterm examination"),
    ("Quiz 1, 2009", "Exams/Quiz1_2009_1.pdf", "University quiz"),
    ("Quiz 1, 2010", "Exams/Quiz1_2010_1.pdf", "University quiz"),
    ("Quiz 1, 2012", "Exams/Quiz1_2012_1.pdf", "University quiz"),
    ("Quiz 2, 2009", "Exams/Quiz2_2009_1.pdf", "University quiz"),
    ("Quiz 2, 2011", "Exams/Quiz2_2011_1.pdf", "University quiz"),
    ("Quiz 2, 2012", "Exams/Quiz2_2012_1.pdf", "University quiz"),
]

LECTURES = [
    (f"Lecture {number}, 2013", f"notes/Lecture_{number}-2013_1.pdf", "University lecture notes")
    for number in range(1, 20)
]
ADDITIONAL = [("Discrete mathematics slide set 5", "notes/dm09_slide5.pdf", "University lecture notes")]
CANDIDATES = ASSESSMENTS + LECTURES + ADDITIONAL


def verify(url: str) -> tuple[int, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "20", "--connect-timeout", "10",
            "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    raw = result.stdout.strip()
    if result.returncode != 0 or "|" not in raw:
        return 0, "unavailable"
    status, content_type = raw.split("|", 1)
    return (int(status) if status.isdigit() else 0, content_type.lower() or "unknown")


def topic_tags(resource_class: str) -> str:
    shared = "discrete mathematics;linear algebra;logic;sets;relations;graphs"
    if "examination" in resource_class:
        return f"{shared};past year questions"
    if "quiz" in resource_class:
        return f"{shared};quiz"
    return f"{shared};lecture notes"


def main() -> None:
    audited: list[tuple[str, str, str, int, str, bool]] = []
    for title, relative_path, resource_class in CANDIDATES:
        url = BASE_URL + relative_path
        status, content_type = verify(url)
        included = status == 200 and "pdf" in content_type
        audited.append((title, url, resource_class, status, content_type, included))

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_title", "resource_url", "http_status", "content_type", "included"])
        for title, url, _resource_class, status, content_type, included in audited:
            writer.writerow([title, url, status, content_type, "Yes" if included else "No"])

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for title, url, resource_class, status, _content_type, included in audited:
            if not included:
                continue
            writer.writerow({
                "country": "Thailand",
                "track": "DM",
                "topic_tags": topic_tags(resource_class),
                "priority": "A",
                "source_type": "First-party university course archive",
                "source_title": "Khon Kaen University — Discrete Mathematics and Linear Algebra (188200)",
                "source_url": SOURCE_URL,
                "resource_title": f"Khon Kaen University — {title}",
                "resource_url": url,
                "resource_class": resource_class,
                "language": "English",
                "notes": "Direct public PDF linked from the English Khon Kaen University 188200 course index. No login or registration is required.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    included_count = sum(item[-1] for item in audited)
    print(f"Wrote {included_count} verified KKU Thailand records to {OUTPUT}")
    print(f"Wrote {len(audited)} item-level URL audits to {AUDIT}")


if __name__ == "__main__":
    main()
