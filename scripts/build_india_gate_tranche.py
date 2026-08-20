"""Verify and promote 100 public GATE question papers from the official IIT Guwahati archive."""

from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
SOURCE = ROOT / "client/src/data/final_resources.csv"
OUTPUT = ROOT / "client/src/data/india_gate_verified_resources.csv"
AUDIT = ROOT / "research/india_gate_url_audit.csv"
GATE_ARCHIVE = "https://gate2026.iitg.ac.in/download.html"


def is_question_paper(row: dict[str, str]) -> bool:
    url = row["resource_url"].lower()
    excluded = ("_key/", "answer_keys", "answerkey", "answer_key", "keys.pdf")
    return (
        row.get("source_title") == "GATE downloads archive"
        and "gate2026.iitg.ac.in/doc/download/" in url
        and re.search(r"/download/20(?:21|22|23|24|25)/", url) is not None
        and url.endswith(".pdf")
        and not any(marker in url for marker in excluded)
    )


def verify(url: str) -> tuple[str, int, str]:
    try:
        response = requests.get(url, timeout=18, stream=True, headers={"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"})
        content_type = response.headers.get("content-type", "")
        response.close()
        return url, response.status_code, content_type
    except requests.RequestException as error:
        return url, 0, type(error).__name__


def paper_year(url: str) -> str:
    match = re.search(r"/download/(20\d{2})/", url)
    return match.group(1) if match else "archive"


def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip() or "GATE discipline"


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        raw = [row for row in csv.DictReader(handle) if is_question_paper(row)]
    unique = {row["resource_url"]: row for row in raw}
    candidates = list(unique.values())
    candidates.sort(key=lambda row: (paper_year(row["resource_url"]), clean_title(row["resource_title"])), reverse=True)
    print(f"Official GATE question-paper candidates: {len(candidates)}")

    audit: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(verify, row["resource_url"]): row["resource_url"] for row in candidates}
        for future in as_completed(futures):
            url, status, content_type = future.result()
            audit[url] = (status, content_type)

    verified = [row for row in candidates if audit[row["resource_url"]][0] == 200]
    verified = verified[:100]
    if len(verified) < 100:
        raise RuntimeError(f"Only {len(verified)} verified GATE question papers; refusing to pad the tranche")

    headers = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in verified:
            year = paper_year(row["resource_url"])
            writer.writerow({
                "country": "India",
                "track": "GA/EM/DM",
                "topic_tags": "general aptitude;engineering mathematics;discrete mathematics;engineering entrance;exam;past-year",
                "priority": "A",
                "source_type": "National examination archive",
                "source_title": "GATE official downloads archive — IIT Guwahati",
                "source_url": GATE_ARCHIVE,
                "resource_title": f"GATE {year} — {clean_title(row['resource_title'])} question paper",
                "resource_url": row["resource_url"],
                "resource_class": "Exam paper",
                "language": "English",
                "notes": "Official GATE question paper from the IIT Guwahati downloads archive. Includes General Aptitude plus paper-specific engineering mathematics or discrete-mathematics content where applicable.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included_in_100"])
        included = {row["resource_url"] for row in verified}
        for row in candidates:
            url = row["resource_url"]
            writer.writerow([url, *audit[url], "Yes" if url in included else "No"])
    print(f"Verified and wrote {len(verified)} distinct India GATE records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
