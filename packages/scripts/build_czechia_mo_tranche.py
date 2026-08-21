"""Build a bounded Czechia tranche from source-published Czech Mathematical Olympiad PDFs.

The script only accepts direct document links whose visible official labels are
"Zadání" (problems) or "Řešení" (solutions). Results, organizational notices,
promotional files, and inferred paths are deliberately excluded.
"""

from __future__ import annotations

import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup


PROJECT = Path("/home/ubuntu/ga-em-dm-resource-hub")
SNAPSHOT_DIR = Path("/home/ubuntu/czechia_mo_html/editions")
DATA_DIR = PROJECT / "apps/web/src/data"
OUTPUT = DATA_DIR / "czechia_mo_verified_resources.csv"
AUDIT = PROJECT / "research/czechia_mo_url_audit.csv"
SOURCE_URL = "https://www.matematickaolympiada.cz/mo-pro-ss/rocnik"
BASE_URL = "https://www.matematickaolympiada.cz"
VERIFY_DATE = "2026-08-14"

ROUND_NAMES = {
    "Domácí kolo": "Home round",
    "Školní kolo": "School round",
    "Krajské kolo": "Regional round",
    "Ústřední kolo": "National final round",
}
MATERIAL_NAMES = {"Zadání": "Official problems", "Řešení": "Official solutions"}


def existing_catalog_urls_and_count() -> tuple[set[str], int]:
    urls: set[str] = set()
    country_count = 0
    for path in DATA_DIR.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = (row.get("resource_url") or "").strip()
                if url:
                    urls.add(url)
                if (row.get("country") or "").strip() == "Czechia" and (row.get("free_resource") or "").strip().lower() == "yes":
                    country_count += 1
    return urls, country_count


def edition_from_path(path: Path) -> int:
    match = re.fullmatch(r"(\d+)-rocnik\.html", path.name)
    if not match:
        raise RuntimeError(f"Unexpected official edition snapshot name: {path.name}")
    return int(match.group(1))


def nearest_round(anchor) -> tuple[str, str]:
    heading = anchor.find_previous(["h3", "h4"])
    while heading is not None:
        label = heading.get_text(" ", strip=True)
        if label in ROUND_NAMES:
            return label, ROUND_NAMES[label]
        heading = heading.find_previous(["h3", "h4"])
    raise RuntimeError("Accepted resource link without a preceding official competition-round heading")


def discover(existing_urls: set[str]) -> list[dict[str, str | int]]:
    candidates: dict[str, dict[str, str | int]] = {}
    for path in sorted(SNAPSHOT_DIR.glob("*-rocnik.html"), key=edition_from_path, reverse=True):
        edition = edition_from_path(path)
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for anchor in soup.select("a[href]"):
            label = " ".join(anchor.get_text(" ", strip=True).split())
            solution_match = re.fullmatch(r"Řešení ([ABC])", label)
            if label not in MATERIAL_NAMES and solution_match is None:
                continue
            href = anchor.get("href", "").strip()
            if not href.lower().endswith(".pdf"):
                raise RuntimeError(f"Official {label} link is not a PDF: {href}")
            url = urljoin(BASE_URL, href)
            if not url.startswith(f"{BASE_URL}/media/"):
                raise RuntimeError(f"Official resource resolves outside document media host: {url}")
            if url in existing_urls or url in candidates:
                continue
            czech_round, english_round = nearest_round(anchor)
            candidates[url] = {
                "url": url,
                "edition": edition,
                "czech_round": czech_round,
                "round": english_round,
                "source_label": label,
                "category": solution_match.group(1) if solution_match else "A/B/C",
                "material": "Official solutions" if solution_match else MATERIAL_NAMES[label],
            }
    return list(candidates.values())


def verify(record: dict[str, str | int]) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "50",
            "--user-agent", "Signal Atlas catalog verifier/1.0", "-o", "/dev/null",
            "-w", "%{http_code}|%{content_type}", str(record["url"]),
        ],
        capture_output=True,
        text=True,
        timeout=65,
        check=False,
    )
    status_text, _, content_type = result.stdout.strip().partition("|")
    return str(record["url"]), int(status_text) if status_text.isdigit() else 0, content_type.lower() or "unknown"


def main() -> None:
    existing_urls, baseline = existing_catalog_urls_and_count()
    required = max(0, 100 - baseline)
    candidates = discover(existing_urls)
    print(f"Czechia baseline: {baseline}; target additions: {required}; official MO candidates: {len(candidates)}")
    if len(candidates) < required:
        raise RuntimeError("Official Czech Mathematical Olympiad archive capacity is below target; refusing to pad Czechia")

    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(verify, record) for record in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)

    verified = [
        record for record in candidates
        if statuses.get(str(record["url"]), (0, ""))[0] == 200
        and "pdf" in statuses.get(str(record["url"]), (0, ""))[1]
    ]
    verified.sort(
        key=lambda record: (
            -int(record["edition"]),
            ["Home round", "School round", "Regional round", "National final round"].index(str(record["round"])),
            0 if record["material"] == "Official problems" else 1,
            str(record["url"]),
        )
    )
    print(f"Individually verified public Czech Olympiad PDFs: {len(verified)}")
    selected = verified[:required]
    if len(selected) < required:
        raise RuntimeError(f"Only {len(selected)} official PDFs verified; refusing to pad Czechia")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in selected:
            is_solution = record["material"] == "Official solutions"
            writer.writerow({
                "country": "Czechia",
                "track": "EM",
                "topic_tags": "engineering mathematics;mathematical olympiad;algebra;geometry;number theory;combinatorics;contest;past paper;solutions",
                "priority": "A",
                "source_type": "National mathematics Olympiad archive",
                "source_title": "Czech Mathematical Olympiad official secondary-school archive",
                "source_url": SOURCE_URL,
                "resource_title": f"Czech Mathematical Olympiad {record['edition']} — {record['round']} — Category {record['category']} — {record['material']}",
                "resource_url": record["url"],
                "resource_class": "Official Olympiad solutions" if is_solution else "Past Olympiad questions",
                "language": "Czech source; English catalog title",
                "notes": f"Direct public {str(record['source_label']).lower()} PDF listed under the official {record['czech_round']} competition section.",
                "access_model": "Free public download",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {str(record["url"]) for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "edition", "official_round", "category", "source_label", "material", "http_status", "content_type", "included"])
        for record in sorted(candidates, key=lambda item: (-int(item["edition"]), str(item["round"]), str(item["material"]), str(item["url"]))):
            status, content_type = statuses.get(str(record["url"]), (0, "not verified"))
            writer.writerow([record["url"], record["edition"], record["czech_round"], record["category"], record["source_label"], record["material"], status, content_type, "Yes" if str(record["url"]) in selected_urls else "No"])
    print(f"Wrote {len(selected)} verified Czech Mathematical Olympiad records to {OUTPUT}")


if __name__ == "__main__":
    main()
