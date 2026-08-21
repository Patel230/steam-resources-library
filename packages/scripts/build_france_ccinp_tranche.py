"""Verify and promote CCINP first-party past question papers for France."""

from __future__ import annotations

import csv
import datetime as dt
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]  # repo root (packages/scripts/ -> root)
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "france_ccinp_verified_resources.csv"
AUDIT = ROOT / "research/france_ccinp_url_audit.csv"
VERIFIED_AT = dt.date.today().isoformat()
TARGET_ADDITIONS = 79
ARCHIVES = {
    "MP": "https://www.concours-commun-inp.fr/fr/epreuves/annales/annales-mp.html",
    "PC": "https://www.concours-commun-inp.fr/fr/epreuves/annales/annales-pc.html",
    "PSI": "https://www.concours-commun-inp.fr/fr/epreuves/annales/annales-psi.html",
    "TSI": "https://www.concours-commun-inp.fr/fr/epreuves/annales/annales-tsi.html",
}
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"})


def existing_free_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT or path.name == "final_resources.csv":
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle) if row.get("resource_url"))
    return urls


def english_subject(context: str) -> tuple[str, str] | None:
    value = context.lower()
    if "math" in value:
        number = " 1" if re.search(r"math.*\b1\b", value) else " 2" if re.search(r"math.*\b2\b", value) else ""
        return f"Mathematics{number}", "EM"
    if "informatique" in value or "information" in value:
        return "Informatics", "DM"
    if "industri" in value:
        return "Industrial Sciences", "EM"
    return None


def candidates() -> list[dict[str, str]]:
    collected: dict[str, dict[str, str]] = {}
    for stream, page_url in ARCHIVES.items():
        response = SESSION.get(page_url, timeout=35)
        if response.status_code != 200:
            print(f"WARN skipped unavailable CCINP page: {page_url} ({response.status_code})")
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        year = ""
        subject_context = ""
        for element in soup.find_all(["h3", "h4", "p", "a"]):
            if element.name == "h3":
                match = re.search(r"(?:Session\s*)?(20\d{2})", element.get_text(" ", strip=True), re.I)
                if match:
                    year = match.group(1)
                continue
            if element.name == "h4":
                subject_context = element.get_text(" ", strip=True)
                continue
            if element.name == "p":
                subject_context = element.get_text(" ", strip=True)
                continue
            href = element.get("href")
            label = element.get_text(" ", strip=True).lower()
            if not href or not year or not href.lower().split("?")[0].endswith(".pdf"):
                continue
            # “Sujet” is the official question-paper label. Reports and response documents are excluded.
            if "sujet" not in label and "subject" not in label:
                continue
            classified = english_subject(subject_context)
            if classified is None:
                continue
            subject, track = classified
            url = requests.compat.urljoin(page_url, href)
            collected[url] = {
                "url": url,
                "stream": stream,
                "year": year,
                "subject": subject,
                "track": track,
                "source_url": page_url,
            }
    return list(collected.values())


def verify(candidate: dict[str, str]) -> tuple[str, int, str]:
    try:
        response = requests.get(candidate["url"], timeout=18, stream=True, headers={"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"})
        content_type = response.headers.get("content-type", "")
        response.close()
        return candidate["url"], response.status_code, content_type
    except requests.RequestException as error:
        return candidate["url"], 0, type(error).__name__


def main() -> None:
    existing = existing_free_urls()
    pool_candidates = [candidate for candidate in candidates() if candidate["url"] not in existing]
    pool_candidates.sort(key=lambda row: (row["year"], row["stream"], row["subject"]), reverse=True)
    print(f"Non-duplicate CCINP question-paper candidates: {len(pool_candidates)}")

    audit: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(verify, candidate): candidate["url"] for candidate in pool_candidates}
        for future in as_completed(futures):
            url, status, content_type = future.result()
            audit[url] = (status, content_type)

    verified = [candidate for candidate in pool_candidates if audit[candidate["url"]][0] == 200][:TARGET_ADDITIONS]
    if len(verified) < TARGET_ADDITIONS:
        raise RuntimeError(f"Only {len(verified)} verified non-duplicate CCINP papers; refusing to pad the tranche")

    headers = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for candidate in verified:
            writer.writerow({
                "country": "France",
                "track": candidate["track"],
                "topic_tags": "engineering mathematics;discrete mathematics;mathematics;informatics;industrial sciences;past year questions;entrance examination",
                "priority": "A",
                "source_type": "National engineering entrance examination archive",
                "source_title": "Concours Commun INP annales (official)",
                "source_url": candidate["source_url"],
                "resource_title": f"CCINP {candidate['stream']} {candidate['year']} — {candidate['subject']} question paper",
                "resource_url": candidate["url"],
                "resource_class": "Past year question paper",
                "language": "French source; English catalog metadata",
                "notes": "Official CCINP past examination paper. The catalog title and description are supplied in English; the original French PDF URL is preserved.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFIED_AT}",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included_in_target"])
        included = {candidate["url"] for candidate in verified}
        for candidate in pool_candidates:
            writer.writerow([candidate["url"], *audit[candidate["url"]], "Yes" if candidate["url"] in included else "No"])
    print(f"Verified and wrote {len(verified)} France CCINP records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
