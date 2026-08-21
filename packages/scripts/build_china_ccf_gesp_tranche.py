from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
SOURCE_DIR = Path("/home/ubuntu/gesp_china_html/sessions")
OUTPUT = DATA / "china_ccf_gesp_verified_resources.csv"
AUDIT = ROOT / "research/china_ccf_gesp_url_audit.csv"
ARCHIVE_URL = "https://gesp.ccf.org.cn/101/1010/index.html"
VERIFY_DATE = "2026-08-14"


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    china_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
                if row.get("country") == "China" and row.get("free_resource") == "Yes":
                    china_count += 1
    return urls, china_count


def session_label(text: str, session_url: str, session_context: str) -> tuple[int, int, str, str]:
    """Return English-facing metadata from an official Chinese archive link label."""
    year_match = re.search(r"(20\d{2})\s*年", text) or re.search(r"(20\d{2})\s*年", session_context) or re.search(r"(20\d{2})-\d{1,2}-\d{1,2}", session_context)
    month_match = re.search(r"(\d{1,2})\s*月", text) or re.search(r"(\d{1,2})\s*月", session_context) or re.search(r"20\d{2}-(\d{1,2})-\d{1,2}", session_context)
    level_match = re.search(r"(\d+)\s*级", text)
    year = int(year_match.group(1)) if year_match else 0
    month = int(month_match.group(1)) if month_match else 0
    level = level_match.group(1) if level_match else ""
    if "图形化" in text:
        stream = "block-based programming"
    elif "Python" in text:
        stream = "Python"
    elif "C++" in text:
        stream = "C++"
    else:
        stream = "programming"
    if not year:
        source_id = Path(session_url).stem
        raise ValueError(f"Missing session year in official link label from {source_id}: {text}")
    return year, month, stream, level


def discover(existing_urls: set[str]) -> list[dict[str, str]]:
    pages = sorted(SOURCE_DIR.glob("*.html"))
    if len(pages) != 15:
        raise RuntimeError(f"Expected 15 official GESP session pages in {SOURCE_DIR}; found {len(pages)}")
    records: dict[str, dict[str, str]] = {}
    for page in pages:
        session_url = f"https://gesp.ccf.org.cn/101/1010/{page.stem}.html"
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        session_context = soup.get_text(" ", strip=True)
        for anchor in soup.select("a[href]"):
            url = anchor.get("href", "").strip()
            if not re.fullmatch(r"https://gesp\.ccf\.org\.cn/101/attach/\d+\.pdf", url):
                continue
            if url in existing_urls:
                continue
            text = anchor.get_text(" ", strip=True)
            year, month, stream, level = session_label(text, session_url, session_context)
            records[url] = {
                "url": url,
                "source_url": session_url,
                "year": str(year),
                "month": str(month),
                "stream": stream,
                "level": level,
                "source_label": text,
            }
    return list(records.values())


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    try:
        response = requests.get(
            record["url"],
            headers={"User-Agent": "Signal Atlas catalog verifier/1.0"},
            timeout=35,
            stream=True,
            allow_redirects=True,
        )
        status = response.status_code
        content_type = response.headers.get("content-type", "").lower()
        response.close()
        return record["url"], status, content_type
    except requests.RequestException as exc:
        return record["url"], 0, f"request error: {type(exc).__name__}"


def main() -> None:
    existing_urls, baseline = existing_catalog()
    required = max(0, 100 - baseline)
    candidates = discover(existing_urls)
    print(f"China baseline: {baseline}; target additions: {required}; CCF GESP non-duplicate candidates: {len(candidates)}")
    if not candidates:
        raise RuntimeError("No non-duplicate CCF GESP candidates found; refusing to write an empty tranche")

    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(verify, candidate) for candidate in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)

    verified = [
        record
        for record in candidates
        if statuses.get(record["url"], (0, ""))[0] == 200
        and "pdf" in statuses.get(record["url"], (0, ""))[1]
    ]
    verified.sort(
        key=lambda record: (int(record["year"]), int(record["month"]), record["stream"], int(record["level"] or 0)),
        reverse=True,
    )
    print(f"CCF GESP individually verified public PDFs: {len(verified)}")
    selected = verified[:required]
    if len(selected) < required:
        raise RuntimeError(
            f"Only {len(selected)} non-duplicate individually verified CCF GESP PDFs; refusing to pad China’s tranche"
        )

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in selected:
            month = record["month"].zfill(2)
            level = f" Level {record['level']}" if record["level"] else ""
            writer.writerow({
                "country": "China",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;exam;mcq",
                "priority": "A",
                "source_type": "National computing association certification archive",
                "source_title": "China Computer Federation GESP past-question archive",
                "source_url": record["source_url"],
                "resource_title": f"CCF GESP {record['stream']}{level} certification paper — {record['year']}-{month}",
                "resource_url": record["url"],
                "resource_class": "Exam paper",
                "language": "Chinese source; English-facing metadata",
                "notes": "Direct public PDF paper listed on the China Computer Federation GESP official past-question archive; original questions are Chinese and catalog metadata is English-facing.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {record["url"] for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "session_url", "source_label", "http_status", "content_type", "included"])
        for record in sorted(candidates, key=lambda item: item["url"]):
            status, content_type = statuses.get(record["url"], (0, "not verified"))
            writer.writerow([record["url"], record["source_url"], record["source_label"], status, content_type, "Yes" if record["url"] in selected_urls else "No"])
    print(f"Wrote {len(selected)} verified CCF GESP records to {OUTPUT}")


if __name__ == "__main__":
    main()
