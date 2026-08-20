"""Verify and promote direct PDF resources from Germany's official BWINF task collection."""

from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
OUTPUT = DATA / "germany_bwinf_verified_resources.csv"
AUDIT = ROOT / "research/germany_verified_url_audit.csv"
ARCHIVE = "https://bwinf.de/bundeswettbewerb/aufgaben/"
MATH_ARCHIVE = "https://www.mathe-wettbewerbe.de/aufgaben"
LEGACY = DATA / "final_resources.csv"
TARGET_ADDITIONS = 89
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


def english_heading(heading: str) -> str:
    match = re.search(r"(\d+)\.\s*Bundeswettbewerb Informatik", heading, re.I)
    return f"German National Informatics Competition {match.group(1)}" if match else "German National Informatics Competition"


def candidates() -> list[dict[str, str]]:
    response = SESSION.get(ARCHIVE, timeout=35)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    collected: dict[str, dict[str, str]] = {}
    for heading in soup.select("h3"):
        section_title = english_heading(heading.get_text(" ", strip=True))
        if section_title == "German National Informatics Competition":
            continue
        sibling = heading.find_next_sibling()
        if sibling is None or sibling.name not in {"ul", "ol"}:
            continue
        for link in sibling.select('a[href$=".pdf"], a[href*=".pdf?"]'):
            href = link.get("href")
            label = link.get_text(" ", strip=True)
            if not href or not label:
                continue
            lower = f"{label} {href}".lower()
            # Exclude administrative cover sheets. Keep official question sheets and solution notes.
            if not any(token in lower for token in ("aufgaben", "lösung", "loesung")) or "mantel" in lower:
                continue
            url = requests.compat.urljoin(ARCHIVE, href)
            kind = "Solution archive" if any(token in lower for token in ("lösung", "loesung")) else "Contest paper"
            round_match = re.search(r"([123])\.?\s*runde", label, re.I)
            round_label = f"Round {round_match.group(1)}" if round_match else "Competition problems"
            collected[url] = {"url": url, "competition": section_title, "round": round_label, "kind": kind}
    return list(collected.values())


def legacy_candidates() -> list[dict[str, str]]:
    """Reuse only direct first-party BWINF links already cataloged from this archive."""
    collected: dict[str, dict[str, str]] = {}
    with LEGACY.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("source_title") != "BWINF task collection":
                continue
            url = row.get("resource_url", "").strip()
            if not (url.startswith("https://bwinf.de/") and ".pdf" in url.lower()):
                continue
            lower = f"{row.get('resource_title', '')} {url}".lower()
            kind = "Solution archive" if any(token in lower for token in ("lösung", "loesung", "solution")) else "Contest paper"
            collected[url] = {
                "url": url,
                "competition": "German National Informatics Competition archive",
                "round": "Official archive entry",
                "kind": kind,
            }
    return list(collected.values())


def mathematics_candidates() -> list[dict[str, str]]:
    """Extract direct public past-round problem and solution PDFs from the official task archive."""
    response = SESSION.get(MATH_ARCHIVE, timeout=35)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    collected: dict[str, dict[str, str]] = {}
    for link in soup.select('a[href$=".pdf"], a[href*=".pdf?"]'):
        href = link.get("href")
        label = link.get_text(" ", strip=True)
        if not href or not label:
            continue
        label_lower = label.lower()
        if not (label_lower.startswith("aufgaben") or label_lower.startswith("lösungen") or label_lower.startswith("loesungen")):
            continue
        url = requests.compat.urljoin(MATH_ARCHIVE, href)
        match = re.search(r"(20\d{2})(?:[._\s-]*([12]))?", label)
        year = match.group(1) if match else "archive"
        round_number = match.group(2) if match and match.group(2) else "past"
        kind = "Solution archive" if label_lower.startswith(("lösungen", "loesungen")) else "Contest paper"
        noun = "solutions" if kind == "Solution archive" else "problem paper"
        collected[url] = {
            "url": url,
            "competition": "German National Mathematics Competition",
            "round": f"{year} Round {round_number} {noun}",
            "kind": kind,
            "math_archive": "yes",
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
    merged = {candidate["url"]: candidate for candidate in candidates()}
    merged.update({candidate["url"]: candidate for candidate in legacy_candidates()})
    merged.update({candidate["url"]: candidate for candidate in mathematics_candidates()})
    pool_candidates = [candidate for candidate in merged.values() if candidate["url"] not in existing]
    pool_candidates.sort(key=lambda row: (row["competition"], row["round"], row["kind"]), reverse=True)
    print(f"Non-duplicate Germany problem/solution candidates: {len(pool_candidates)}")

    audit: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(verify, candidate): candidate["url"] for candidate in pool_candidates}
        for future in as_completed(futures):
            url, status, content_type = future.result()
            audit[url] = (status, content_type)

    verified = [candidate for candidate in pool_candidates if audit[candidate["url"]][0] == 200][:TARGET_ADDITIONS]
    if len(verified) < TARGET_ADDITIONS:
        raise RuntimeError(f"Only {len(verified)} verified non-duplicate BWINF records; refusing to pad the tranche")

    headers = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for candidate in verified:
            noun = "solution notes" if candidate["kind"] == "Solution archive" else "problem sheet"
            is_math = candidate.get("math_archive") == "yes"
            writer.writerow({
                "country": "Germany",
                "track": "EM/DM" if is_math else "DM",
                "topic_tags": "engineering mathematics;discrete mathematics;mathematical problem solving;contest;solution" if is_math else "discrete mathematics;algorithms;informatics;problem solving;programming contest;contest;solution",
                "priority": "A",
                "source_type": "National mathematics competition archive" if is_math else "National informatics competition archive",
                "source_title": "German national mathematics competitions task archive (official)" if is_math else "BWINF task collection (official)",
                "source_url": MATH_ARCHIVE if is_math else ARCHIVE,
                "resource_title": f"{candidate['competition']} — {candidate['round']}" if is_math else f"{candidate['competition']} — {candidate['round']} {noun}",
                "resource_url": candidate["url"],
                "resource_class": candidate["kind"],
                "language": "German source; English catalog metadata",
                "notes": "Official German mathematics competition material. The catalog title and description are supplied in English; the original German PDF URL is preserved." if is_math else "Official German National Informatics Competition material. The catalog title and description are supplied in English; the original German PDF URL is preserved.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-14",
                "free_resource": "Yes",
            })
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "http_status", "content_type", "included_in_100"])
        included = {candidate["url"] for candidate in verified}
        for candidate in pool_candidates:
            writer.writerow([candidate["url"], *audit[candidate["url"]], "Yes" if candidate["url"] in included else "No"])
    print(f"Verified and wrote {len(verified)} Germany records to {OUTPUT}")
    print(f"Audit written to {AUDIT}")


if __name__ == "__main__":
    main()
