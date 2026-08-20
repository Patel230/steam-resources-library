from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
ARCHIVE_HTML = Path("/home/ubuntu/omm_mexico_html/canguro_index.html")
OUTPUT = DATA / "mexico_omm_canguro_verified_resources.csv"
AUDIT = ROOT / "research/mexico_omm_canguro_url_audit.csv"
ARCHIVE_URL = "https://www.ommenlinea.org/actividades/concursos/canguro-matematico/"
VERIFY_DATE = "2026-08-14"
BASE_URL = "https://www.ommenlinea.org"


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    mexico_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
                if row.get("country") == "Mexico" and row.get("free_resource") == "Yes":
                    mexico_count += 1
    return urls, mexico_count


def level_from_heading(text: str) -> str | None:
    text = re.sub(r"\s+", " ", text).strip().lower()
    if "nivel escolar" in text:
        return "School"
    if "nivel benjam" in text:
        return "Benjamin"
    if "nivel cadete" in text:
        return "Cadet"
    if "nivel estudiante" in text:
        return "Student"
    return None


def discover(existing_urls: set[str]) -> list[dict[str, str]]:
    if not ARCHIVE_HTML.exists():
        raise RuntimeError(f"Missing official Canguro archive snapshot: {ARCHIVE_HTML}")
    soup = BeautifulSoup(ARCHIVE_HTML.read_text(encoding="utf-8"), "html.parser")
    records: dict[str, dict[str, str]] = {}
    level: str | None = None
    latest_year: str | None = None

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "li"]):
        if tag.name != "li":
            detected = level_from_heading(tag.get_text(" ", strip=True))
            if detected:
                level = detected
                latest_year = None
            continue

        classes = set(tag.get("class", []))
        if not ({"problemas", "soluciones"} & classes):
            continue
        link = tag.find("a", href=True)
        if not link:
            continue
        href = link["href"].strip()
        if not re.fullmatch(r"/wp-content/uploads/practica/canguro/[A-Za-z0-9_-]+\.pdf", href):
            continue
        if not level:
            raise RuntimeError(f"Canguro PDF lacks a source-published level heading: {href}")
        label = link.get_text(" ", strip=True)
        if "problemas" in classes:
            if not re.fullmatch(r"20\d{2}", label):
                raise RuntimeError(f"Canguro question link lacks its source-published year: {href} ({label!r})")
            latest_year = label
            material = "Exam paper"
        else:
            if not latest_year:
                raise RuntimeError(f"Canguro solution has no preceding source-published exam year: {href}")
            material = "Solution key"

        url = urljoin(BASE_URL, href)
        if url in existing_urls:
            continue
        if url in records:
            raise RuntimeError(f"Duplicate Canguro direct URL in source archive: {url}")
        records[url] = {
            "url": url,
            "year": latest_year,
            "level": level,
            "material": material,
            "source_label": label,
        }

    if len(records) < 100:
        raise RuntimeError(f"Expected a deep official Canguro archive, found only {len(records)} candidates")
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
    print(f"Mexico baseline: {baseline}; target additions: {required}; OMM Canguro non-duplicate candidates: {len(candidates)}")
    if not candidates:
        raise RuntimeError("No non-duplicate OMM Canguro candidates found; refusing to write an empty tranche")

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
    level_rank = {"Student": 4, "Cadet": 3, "Benjamin": 2, "School": 1}
    material_rank = {"Exam paper": 1, "Solution key": 0}
    verified.sort(
        key=lambda record: (
            int(record["year"]),
            level_rank[record["level"]],
            material_rank[record["material"]],
            record["url"],
        ),
        reverse=True,
    )
    print(f"OMM Canguro individually verified public PDFs: {len(verified)}")
    selected = verified[:required]
    if len(selected) < required:
        raise RuntimeError(
            f"Only {len(selected)} non-duplicate individually verified Canguro PDFs; refusing to pad Mexico’s tranche"
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
            material_label = "past exam" if record["material"] == "Exam paper" else "official solutions"
            writer.writerow({
                "country": "Mexico",
                "track": "GA",
                "topic_tags": "general aptitude;mathematics;problem-solving;contest;exam;mcq;solutions",
                "priority": "A",
                "source_type": "National mathematics Olympiad competition archive",
                "source_title": "Mexican Mathematical Olympiad Canguro archive",
                "source_url": ARCHIVE_URL,
                "resource_title": f"Mexican Canguro Mathematics {record['level']} level {material_label} — {record['year']}",
                "resource_url": record["url"],
                "resource_class": record["material"],
                "language": "Spanish source; English-facing metadata",
                "notes": "Direct public PDF listed in the Mexican Mathematical Olympiad’s official Canguro past-exam archive; original questions and solutions are in Spanish and catalog metadata is English-facing.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {record["url"] for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "year", "level", "material", "source_label", "http_status", "content_type", "included"])
        for record in sorted(candidates, key=lambda item: item["url"]):
            status, content_type = statuses.get(record["url"], (0, "not verified"))
            writer.writerow([
                record["url"], record["year"], record["level"], record["material"], record["source_label"],
                status, content_type, "Yes" if record["url"] in selected_urls else "No",
            ])
    print(f"Wrote {len(selected)} verified OMM Canguro records to {OUTPUT}")


if __name__ == "__main__":
    main()
