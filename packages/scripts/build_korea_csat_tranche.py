from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "republic_of_korea_kice_csat_verified_resources.csv"
AUDIT = ROOT / "research/republic_of_korea_kice_csat_url_audit.csv"
DOWNLOAD_PREFIX = "https://www.suneung.re.kr/boardCnts/fileDown.do?fileSeq="
VERIFY_DATE = "2026-08-14"

# These local source snapshots were retrieved directly from KICE's rendered public
# archives. They are used to preserve exact attachment IDs; URL patterns are never inferred.
ARCHIVES = (
    {
        "kind": "CSAT",
        "source_url": "https://www.suneung.re.kr/boardCnts/list.do?boardID=1500234&m=0403&s=suneung",
        "html_dir": Path("/home/ubuntu/kice_archive_html"),
        "pages": 18,
        "field_index": 2,
        "date_index": 4,
        "period_index": None,
    },
    {
        "kind": "CSAT mock evaluation",
        "source_url": "https://www.suneung.re.kr/boardCnts/list.do?boardID=1500236&m=0403&s=suneung",
        "html_dir": Path("/home/ubuntu/kice_mock_html"),
        "pages": 37,
        "field_index": 3,
        "date_index": 5,
        "period_index": 2,
    },
)


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
                if row.get("country") == "Republic of Korea" and row.get("free_resource") == "Yes":
                    country_count += 1
    return urls, country_count


def classify_filename(filename: str) -> tuple[str, str] | None:
    """Classify only KICE's explicitly named mathematics papers and answer tables."""
    if "문제지" in filename:
        return "Exam paper", "question paper"
    if "정답" in filename:
        return "Solution archive", "answer key"
    return None


def numbered_pages(archive: dict[str, object]) -> list[Path]:
    html_dir = archive["html_dir"]
    assert isinstance(html_dir, Path)
    expected = int(archive["pages"])
    pages = sorted(html_dir.glob("page_*.html"), key=lambda path: int(re.search(r"(\d+)", path.stem).group(1)))
    if len(pages) != expected:
        raise RuntimeError(f"Expected {expected} official KICE pages in {html_dir}; found {len(pages)}")
    return pages


def discover(existing_urls: set[str]) -> list[dict[str, str]]:
    discovered: dict[str, dict[str, str]] = {}
    for archive in ARCHIVES:
        kind = str(archive["kind"])
        source_url = str(archive["source_url"])
        field_index = int(archive["field_index"])
        date_index = int(archive["date_index"])
        period_index = archive["period_index"]
        for page in numbered_pages(archive):
            soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
            for row in soup.select("table tbody tr"):
                cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
                if len(cells) <= max(field_index, date_index) or cells[field_index] != "수학" or not re.fullmatch(r"20\d{2}", cells[1]):
                    continue
                year = cells[1]
                period = cells[int(period_index)] if isinstance(period_index, int) and len(cells) > period_index else ""
                published = cells[date_index]
                for anchor in row.select("a[onclick*='fn_fileDown']"):
                    handler = anchor.get("onclick", "")
                    match = re.search(r"'([a-f0-9]{32})'", handler)
                    filename = anchor.get("title", "").strip()
                    category = classify_filename(filename)
                    if not match or not category:
                        continue
                    resource_url = f"{DOWNLOAD_PREFIX}{match.group(1)}"
                    if resource_url in existing_urls:
                        continue
                    resource_class, descriptor = category
                    discovered[resource_url] = {
                        "url": resource_url,
                        "year": year,
                        "period": period,
                        "published": published,
                        "kind": kind,
                        "source_url": source_url,
                        "resource_class": resource_class,
                        "descriptor": descriptor,
                        "source_filename": filename,
                    }
    return list(discovered.values())


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
    needed = max(0, 100 - baseline)
    candidates = discover(existing_urls)
    print(f"Republic of Korea baseline: {baseline}; target additions: {needed}; KICE non-duplicate candidates: {len(candidates)}")
    if not candidates:
        raise RuntimeError("No non-duplicate KICE candidates found; refusing to write an empty tranche")

    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(verify, candidate) for candidate in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)

    records = [
        candidate
        for candidate in candidates
        if statuses.get(candidate["url"], (0, ""))[0] == 200
        and "pdf" in statuses.get(candidate["url"], (0, ""))[1]
    ]
    records.sort(
        key=lambda record: (
            int(record["year"]),
            1 if record["resource_class"] == "Exam paper" else 0,
            record["kind"],
            record["period"],
            record["descriptor"],
        ),
        reverse=True,
    )
    print(f"KICE individually verified public PDFs: {len(records)}")
    selected = records[:needed]
    if len(selected) < needed:
        raise RuntimeError(
            f"Only {len(selected)} non-duplicate, individually verified KICE mathematics PDFs; refusing to pad Republic of Korea's tranche"
        )

    columns = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in selected:
            period = f" {record['period']}" if record["period"] else ""
            writer.writerow({
                "country": "Republic of Korea",
                "track": "EM",
                "topic_tags": "engineering mathematics;algebra;calculus;probability;exam;past-year;answer-key",
                "priority": "A",
                "source_type": "National assessment authority archive",
                "source_title": f"Korea Institute of Curriculum & Evaluation {record['kind']} mathematics archive",
                "source_url": record["source_url"],
                "resource_title": f"KICE {record['kind']} Mathematics {record['year']}{period} — official {record['descriptor']}",
                "resource_url": record["url"],
                "resource_class": record["resource_class"],
                "language": "Korean source; English-facing metadata",
                "notes": "Direct public PDF listed in KICE's official mathematics archive; original exam material is Korean and catalog metadata is English-facing.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {record["url"] for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "archive", "source_filename", "http_status", "content_type", "included"])
        for candidate in sorted(candidates, key=lambda item: item["url"]):
            status, content_type = statuses.get(candidate["url"], (0, "not verified"))
            writer.writerow([candidate["url"], candidate["kind"], candidate["source_filename"], status, content_type, "Yes" if candidate["url"] in selected_urls else "No"])
    print(f"Wrote {len(selected)} verified KICE records to {OUTPUT}")


if __name__ == "__main__":
    main()
