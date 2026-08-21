from __future__ import annotations

import csv
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


"""Signal Atlas data style: source-led, English-facing, and access-audited.

This builder reads only official Asia e University ExamQ OAI-PMH metadata, keeps
the exact public PDF identifier published in each record, and verifies each
candidate independently before writing catalog rows. It never infers PDF paths.
"""

ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "malaysia_aeu_examq_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_aeu_examq_url_audit.csv"
OAI_URL = "http://examq.aeu.edu.my/cgi/oai2"
PUBLISHED_SET = "7374617475733D707562"
VERIFY_DATE = "2026-08-15"

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

TARGET_RE = re.compile(
    r"\b("
    r"engineering mathematics|applied mathematics|discrete mathematics|advanced discrete mathematics|"
    r"linear algebra|calculus|differential equations?|numerical methods?|probability|statistics|"
    r"operations research|algorithms?|data structures?"
    r")\b",
    re.IGNORECASE,
)
EM_RE = re.compile(r"engineering mathematics|applied mathematics|linear algebra|calculus|differential|numerical|statistics?|probability|operations research", re.IGNORECASE)
DM_RE = re.compile(r"discrete mathematics|algorithms?|data structures?", re.IGNORECASE)


def catalog_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle))
    return urls


def fetch_xml(params: dict[str, str]) -> ET.Element:
    url = f"{OAI_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "SignalAtlas/1.0 (+public-resource-audit)"})
    with urlopen(request, timeout=45) as response:
        return ET.fromstring(response.read())


def text_values(node: ET.Element, name: str) -> list[str]:
    return [value.text.strip() for value in node.findall(f".//dc:{name}", NS) if value.text and value.text.strip()]


def source_records() -> list[dict[str, str]]:
    params = {"verb": "ListRecords", "metadataPrefix": "oai_dc", "set": PUBLISHED_SET}
    records: dict[str, dict[str, str]] = {}
    pages = 0
    while True:
        root = fetch_xml(params)
        error = root.find(".//oai:error", NS)
        if error is not None:
            raise RuntimeError(f"OAI-PMH error: {(error.text or '').strip()}")
        for record in root.findall(".//oai:record", NS):
            header = record.find("oai:header", NS)
            if header is None or header.attrib.get("status") == "deleted":
                continue
            title = next(iter(text_values(record, "title")), "")
            if not title or not TARGET_RE.search(title):
                continue
            identifiers = text_values(record, "identifier")
            pdf_urls = [
                url for url in identifiers
                if url.startswith("http://examq.aeu.edu.my/id/eprint/") and url.lower().endswith(".pdf")
            ]
            if not pdf_urls:
                continue
            dates = text_values(record, "date")
            year_match = re.search(r"(?:19|20)\d{2}", " ".join(dates))
            for resource_url in pdf_urls:
                records[resource_url] = {
                    "title": " ".join(title.split()),
                    "year": year_match.group(0) if year_match else "Undated",
                    "resource_url": resource_url,
                }
        token_node = root.find(".//oai:resumptionToken", NS)
        token = (token_node.text or "").strip() if token_node is not None else ""
        pages += 1
        if not token:
            break
        if pages > 200:
            raise RuntimeError("OAI-PMH pagination exceeded safe 200-page bound")
        params = {"verb": "ListRecords", "resumptionToken": token}
        time.sleep(0.05)
    return sorted(records.values(), key=lambda row: (row["year"], row["title"], row["resource_url"]), reverse=True)


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "30",
            "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}",
            record["resource_url"],
        ],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    response = result.stdout.strip()
    if result.returncode != 0 or "|" not in response:
        return record["resource_url"], 0, "unavailable"
    code, content_type = response.split("|", 1)
    return record["resource_url"], int(code) if code.isdigit() else 0, content_type.lower() or "unknown"


def classification(title: str) -> tuple[str, str, str]:
    if DM_RE.search(title) and not EM_RE.search(title):
        return "DM", "algorithms;computing;discrete mathematics;university examination", "Discrete Mathematics / Computing"
    if DM_RE.search(title) and EM_RE.search(title):
        return "DM", "algorithms;mathematics;computing;university examination", "Mathematics / Computing"
    return "EM", "engineering mathematics;mathematics;university examination", "Engineering Mathematics"


def main() -> None:
    existing = catalog_urls()
    discovered = source_records()
    candidates = [record for record in discovered if record["resource_url"] not in existing]
    print(f"Official AEU OAI target-subject non-duplicate candidates: {len(candidates)}")

    results: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(verify, candidate) for candidate in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            results[url] = (status, content_type)

    verified = [
        record for record in candidates
        if results.get(record["resource_url"], (0, ""))[0] == 200
        and "pdf" in results[record["resource_url"]][1]
    ]
    print(f"Individually verified public AEU PDF resources: {len(verified)}")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in verified:
            track, tags, route = classification(record["title"])
            writer.writerow({
                "country": "Malaysia",
                "track": track,
                "topic_tags": tags,
                "priority": "A",
                "source_type": "University past examination archive",
                "source_title": "Asia e University ExamQ past examination repository",
                "source_url": OAI_URL,
                "resource_title": f"{record['year']} — Asia e University — {route} — {record['title']}",
                "resource_url": record["resource_url"],
                "resource_class": "University past examination paper",
                "language": "English",
                "notes": "Public PDF identifier published in the official Asia e University ExamQ OAI-PMH record; title is translated only for archive context where needed.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "source_title", "year", "http_status", "content_type", "included"])
        for record in candidates:
            status, content_type = results.get(record["resource_url"], (0, "unavailable"))
            writer.writerow([
                record["resource_url"], record["title"], record["year"], status, content_type,
                "Yes" if record in verified else "No",
            ])
    print(f"Wrote {len(verified)} verified Asia e University records to {OUTPUT}")


if __name__ == "__main__":
    main()
