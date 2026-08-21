"""Build a verified Indonesia tranche from the public TOKI download index.

Only direct download-manager URLs visibly published by Tim Olimpiade Komputer
Indonesia (TOKI) are considered. Each actual content response is checked before
it becomes a catalog row; source landing pages and non-content responses remain
in the audit only.
"""

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "indonesia_toki_verified_resources.csv"
AUDIT = ROOT / "research/indonesia_toki_url_audit.csv"
INDEX_URL = "https://toki.id/downloads/"
VERIFY_DATE = "2026-08-14"
REQUEST_HEADERS = {"User-Agent": "Signal Atlas catalog verifier/1.0 (+public-resource-audit)"}

ROUND_RE = re.compile(r"^(osk|osp|osn)-(20\d{2})(?:-|$)")


def existing_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
    return urls


def fetch(url: str) -> requests.Response:
    return requests.get(url, headers=REQUEST_HEADERS, timeout=35, allow_redirects=True)


def source_pages() -> list[tuple[str, str, str]]:
    response = fetch(INDEX_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    pages: dict[str, tuple[str, str, str]] = {}
    for anchor in soup.select("a[href]"):
        href = urljoin(INDEX_URL, anchor.get("href", "").strip())
        if not href.startswith("https://toki.id/download/"):
            continue
        slug = href.rstrip("/").rsplit("/", 1)[-1]
        round_match = ROUND_RE.match(slug)
        if round_match:
            round_code, year = round_match.groups()
            labels = {
                "osk": "City/District Selection",
                "osp": "Provincial Selection",
                "osn": "National Science Olympiad",
            }
            title = f"TOKI {labels[round_code]} informatics contest package — {year}"
            pages[href] = (slug, title, "Olympiad question package")
    return sorted(pages.values(), key=lambda item: item[0])


def discover(existing: set[str]) -> list[dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for slug, title, resource_class in source_pages():
        source_url = f"https://toki.id/download/{slug}/"
        response = fetch(source_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = {
            urljoin(source_url, anchor.get("href", "").strip())
            for anchor in soup.select("a[href*='wpdmdl=']")
        }
        links.update(
            urljoin(source_url, match.group(1).replace("&amp;", "&"))
            for anchor in soup.select("a[onclick]")
            for match in re.finditer(r"location\.href='([^']*wpdmdl=[^']+)'", anchor.get("onclick", ""))
        )
        if len(links) != 1:
            raise RuntimeError(f"Expected exactly one source-published download link at {source_url}; found {len(links)}")
        resource_url = next(iter(links))
        if resource_url not in existing:
            records[resource_url] = {
                "source_url": source_url,
                "resource_url": resource_url,
                "source_label": title,
                "resource_class": resource_class,
            }
    return list(records.values())


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    try:
        response = fetch(record["resource_url"])
        status = response.status_code
        content_type = response.headers.get("content-type", "").lower()
        response.close()
        return record["resource_url"], status, content_type
    except requests.RequestException as exc:
        return record["resource_url"], 0, f"request error: {type(exc).__name__}"


def main() -> None:
    candidates = discover(existing_urls())
    if not candidates:
        raise RuntimeError("No non-duplicate source-published TOKI candidates found; refusing to write an empty tranche")
    print(f"TOKI source-published non-duplicate candidates: {len(candidates)}")

    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(verify, record) for record in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)

    allowed_types = ("pdf", "zip", "octet-stream", "msword", "officedocument")
    verified = [
        record for record in candidates
        if statuses.get(record["resource_url"], (0, ""))[0] == 200
        and any(token in statuses[record["resource_url"]][1] for token in allowed_types)
    ]
    if not verified:
        raise RuntimeError("TOKI candidates did not return public document content; refusing to promote landing pages")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in sorted(verified, key=lambda item: item["source_label"]):
            writer.writerow({
                "country": "Indonesia",
                "track": "DM",
                "topic_tags": "discrete mathematics;algorithms;programming;logic;problem-solving;contest;olympiad;solution",
                "priority": "A",
                "source_type": "National informatics olympiad organiser archive",
                "source_title": "Tim Olimpiade Komputer Indonesia (TOKI) downloads archive",
                "source_url": record["source_url"],
                "resource_title": record["source_label"],
                "resource_url": record["resource_url"],
                "resource_class": record["resource_class"],
                "language": "Indonesian source; English-facing metadata",
                "notes": "Direct public downloadable contest package or study document visibly published on the Tim Olimpiade Komputer Indonesia official archive; original material may be Indonesian and catalog metadata is English-facing.",
                "access_model": "Free public download",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {record["resource_url"] for record in verified}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "source_url", "source_label", "http_status", "content_type", "included"])
        for record in sorted(candidates, key=lambda item: item["resource_url"]):
            status, content_type = statuses.get(record["resource_url"], (0, "not verified"))
            writer.writerow([record["resource_url"], record["source_url"], record["source_label"], status, content_type, "Yes" if record["resource_url"] in selected_urls else "No"])
    print(f"Individually verified public TOKI resources: {len(verified)}")
    print(f"Wrote {len(verified)} Indonesia TOKI records to {OUTPUT}")


if __name__ == "__main__":
    main()
