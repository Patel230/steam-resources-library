from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "australia_scsa_verified_resources.csv"
AUDIT = ROOT / "research/australia_scsa_url_audit.csv"

# Each inventory was extracted directly from the rendered first-party archive; the
# paired payload is a browser-session HEAD check for those exact discovered URLs.
ARCHIVES = (
    (
        "Mathematics Applications",
        "https://senior-secondary.scsa.wa.edu.au/further-resources/past-atar-course-exams/mathematics-past-atar-course-exams",
        Path("/home/ubuntu/console_outputs/exec_result_2026-08-14_19-36-47_155.txt"),
        Path("/home/ubuntu/console_outputs/exec_result_2026-08-14_19-41-02_278.txt"),
    ),
    (
        "Mathematics Methods",
        "https://senior-secondary.scsa.wa.edu.au/further-resources/past-atar-course-exams/mathematics-methods-past-atar-course-exams",
        Path("/home/ubuntu/console_outputs/exec_result_2026-08-14_19-37-45_466.txt"),
        Path("/home/ubuntu/console_outputs/exec_result_2026-08-14_19-40-25_333.txt"),
    ),
    (
        "Mathematics Specialist",
        "https://senior-secondary.scsa.wa.edu.au/further-resources/past-atar-course-exams/mathematics-specialist-past-atar-course-exams",
        Path("/home/ubuntu/console_outputs/exec_result_2026-08-14_19-39-04_868.txt"),
        Path("/home/ubuntu/console_outputs/exec_result_2026-08-14_19-39-29_867.txt"),
    ),
)


def read_console_payload(path: Path) -> list[dict[str, object]]:
    """Decode the browser-console JSON string saved by the browsing environment."""
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, list):
        raise ValueError(f"Unexpected browser payload shape in {path}")
    return [entry for entry in raw if isinstance(entry, dict)]


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    country_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
                if row.get("country") == "Australia" and row.get("free_resource") == "Yes":
                    country_count += 1
    return urls, country_count


def clean_label(label: object) -> str:
    text = re.sub(r"\s+", " ", str(label)).strip()
    text = re.sub(r"^PDF\s+", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+opens in new window$", "", text, flags=re.IGNORECASE)


def classify(label: str) -> tuple[str, str] | None:
    normalized = label.lower()
    if "formula" in normalized:
        return None
    if "marking key" in normalized:
        return "Solution archive", "marking key"
    if "examination report" in normalized:
        return "Solution archive", "candidate examination report"
    if "examination" in normalized:
        return "Exam paper", "examination paper"
    return None


def discover(existing_urls: set[str]) -> tuple[list[dict[str, str]], dict[str, tuple[int, str]]]:
    documents: dict[str, dict[str, str]] = {}
    statuses: dict[str, tuple[int, str]] = {}

    for subject, archive_url, inventory_path, verification_path in ARCHIVES:
        verification = {
            str(entry.get("url", "")): (int(entry.get("status", 0)), str(entry.get("type", "")))
            for entry in read_console_payload(verification_path)
            if str(entry.get("url", ""))
        }
        for entry in read_console_payload(inventory_path):
            url = str(entry.get("url", "")).strip()
            label = clean_label(entry.get("label", ""))
            year = str(entry.get("year", "")).strip()
            category = classify(label)
            if not url or not category or not re.fullmatch(r"20\d{2}", year):
                continue
            status, content_type = verification.get(url, (0, "not browser-verified"))
            statuses[url] = (status, content_type)
            if url in existing_urls or status != 200 or "pdf" not in content_type.lower():
                continue
            resource_class, descriptor = category
            documents[url] = {
                "url": url,
                "subject": subject,
                "year": year,
                "descriptor": descriptor,
                "resource_class": resource_class,
                "source_url": archive_url,
            }

    return list(documents.values()), statuses


def main() -> None:
    existing_urls, baseline = existing_catalog()
    needed = max(0, 100 - baseline)
    records, statuses = discover(existing_urls)
    records.sort(key=lambda record: (int(record["year"]), record["subject"], record["descriptor"]), reverse=True)
    print(f"Australia baseline: {baseline}; target additions: {needed}; browser-verified non-duplicates: {len(records)}")
    selected = records[:needed]
    if len(selected) < needed:
        raise RuntimeError(f"Only {len(selected)} browser-verified public SCSA documents; refusing to pad Australia's tranche")

    columns = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in selected:
            writer.writerow({
                "country": "Australia",
                "track": "EM",
                "topic_tags": "engineering mathematics;calculus;statistics;probability;mathematical methods;specialist mathematics;exam;past paper;solution",
                "priority": "A",
                "source_type": "State curriculum authority examination archive",
                "source_title": "Western Australian SCSA Mathematics ATAR past examinations and marking keys",
                "source_url": record["source_url"],
                "resource_title": f"Western Australia ATAR {record['subject']} {record['year']} — official {record['descriptor']}",
                "resource_url": record["url"],
                "resource_class": record["resource_class"],
                "language": "English",
                "notes": "Official state assessment archive entry; public PDF access browser-validated after command-line anti-bot challenge.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })

    selected_urls = {record["url"] for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included"])
        for url in sorted(statuses):
            status, content_type = statuses[url]
            writer.writerow([url, status, content_type, "Yes" if url in selected_urls else "No"])
    print(f"Wrote {len(selected)} browser-verified SCSA records to {OUTPUT}")


if __name__ == "__main__":
    main()
