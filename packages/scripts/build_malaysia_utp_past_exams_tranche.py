from __future__ import annotations

import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
SNAPSHOTS = Path("/home/ubuntu/utp_malaysia_html")
OUTPUT = DATA / "malaysia_utp_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_utp_url_audit.csv"
VERIFY_DATE = "2026-08-14"

EPRINT_RE = re.compile(r"https?://utpedia\.utp\.edu\.my/id/eprint/(\d+)/?$")
PDF_RE = re.compile(r"https?://utpedia\.utp\.edu\.my/id/eprint/\d+/1/[^\s\"<>]+\.pdf(?:\?[^\s\"<>]+)?$", re.I)

RULES: list[tuple[re.Pattern[str], str, str, str]] = [
    (re.compile(r"\b(discrete mathematics|algorithm|data structure|programming|computer systems|information security|artificial intelligence|data mining|knowledge discovery|computing security)\b", re.I), "DM", "discrete mathematics;algorithms;computing;past paper", "Discrete mathematics or computing"),
    (re.compile(r"\b(engineering mathematics|fundamental mathematics|mathematics [I1V]|linear algebra|numerical|probability|statistics|quantitative|operations research|modelling and simulation|data analytics|decision making)\b", re.I), "EM", "engineering mathematics;quantitative methods;past paper", "Engineering mathematics or quantitative methods"),
    (re.compile(r"\b(thinking skills|business mathematics|management science|engineering economics)\b", re.I), "GA", "general aptitude;quantitative reasoning;past paper", "General aptitude or quantitative reasoning"),
]


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    malaysia_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
                if row.get("country") == "Malaysia" and row.get("free_resource", "").strip().lower() == "yes":
                    malaysia_count += 1
    return urls, malaysia_count


def classify(title: str) -> tuple[str, str, str] | None:
    for pattern, track, tags, family in RULES:
        if pattern.search(title):
            return track, tags, family
    return None


def normalize_eprint(href: str) -> tuple[str, str] | None:
    url = href.strip().replace("http://", "https://")
    match = EPRINT_RE.fullmatch(url)
    if not match:
        return None
    return url, match.group(1)


def discover(existing_urls: set[str]) -> list[dict[str, str]]:
    candidates: dict[str, dict[str, str]] = {}
    for year in (2022, 2023, 2024, 2025):
        snapshot = SNAPSHOTS / f"{year}.html"
        if not snapshot.exists():
            raise RuntimeError(f"Missing official UTPedia source snapshot: {snapshot}")
        soup = BeautifulSoup(snapshot.read_text(encoding="utf-8"), "html.parser")
        source_url = f"https://utpedia.utp.edu.my/view/types/exam/{year}.type.html"
        for anchor in soup.select('a[href*="/id/eprint/"]'):
            normalized = normalize_eprint(anchor.get("href", ""))
            if not normalized:
                continue
            eprint_url, eprint_id = normalized
            title = " ".join(anchor.get_text(" ", strip=True).split())
            context = " ".join(anchor.parent.get_text(" ", strip=True).split()) if anchor.parent else title
            if not title or "unpublished" in context.lower():
                continue
            classification = classify(title)
            if not classification:
                continue
            track, tags, family = classification
            key = eprint_id
            record = {
                "eprint_id": eprint_id,
                "eprint_url": eprint_url,
                "source_url": source_url,
                "year": str(year),
                "course_title": title.rstrip("."),
                "track": track,
                "topic_tags": tags,
                "family": family,
            }
            if key in candidates and candidates[key] != record:
                raise RuntimeError(f"Conflicting official list metadata for UTPedia eprint {eprint_id}")
            candidates[key] = record
    return list(candidates.values())


def fetch_direct_pdf(record: dict[str, str]) -> tuple[str, str, int, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--fail", "--silent", "--show-error", "--max-time", "12",
            "--user-agent", "Signal Atlas catalog verifier/1.0", record["eprint_url"],
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if result.returncode != 0:
        return record["eprint_id"], "", 0, "eprint page unavailable"
    soup = BeautifulSoup(result.stdout, "html.parser")
    direct_urls = {
        urljoin(record["eprint_url"], anchor["href"].strip()).replace("http://", "https://")
        for anchor in soup.select("a[href]")
        if PDF_RE.fullmatch(urljoin(record["eprint_url"], anchor["href"].strip()).replace("http://", "https://"))
    }
    if len(direct_urls) != 1:
        return record["eprint_id"], "", 0, f"expected one official PDF, found {len(direct_urls)}"
    return record["eprint_id"], direct_urls.pop(), 200, "eprint page HTTP 200"


def verify_pdf(record: dict[str, str]) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "wget", "--server-response", "--spider", "--timeout=12", "--tries=1",
            "--user-agent=Signal Atlas catalog verifier/1.0", record["resource_url"],
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    transcript = f"{result.stdout}\n{result.stderr}"
    statuses = re.findall(r"HTTP/\S+\s+(\d{3})", transcript)
    content_types = re.findall(r"Content-Type:\s*([^\r\n;]+)", transcript, flags=re.I)
    return record["eprint_id"], int(statuses[-1]) if statuses else 0, content_types[-1].lower() if content_types else "unknown"


def main() -> None:
    existing_urls, baseline = existing_catalog()
    required = max(0, 100 - baseline)
    candidates = discover(existing_urls)
    print(f"Malaysia baseline: {baseline}; target additions: {required}; source-listed target candidates: {len(candidates)}")
    if len(candidates) < required:
        raise RuntimeError("UTPedia target-course capacity is below the Malaysia target; refusing to pad")

    verification_pool = sorted(
        candidates,
        key=lambda item: (int(item["year"]), int(item["eprint_id"])),
        reverse=True,
    )[: max(required * 2, 160)]
    print(f"Bounded newest-first UTPedia verification pool: {len(verification_pool)}")

    resolved: dict[str, tuple[str, int, str]] = {}
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_direct_pdf, record) for record in verification_pool]
        for future in as_completed(futures):
            eprint_id, direct_url, status, note = future.result()
            resolved[eprint_id] = (direct_url, status, note)

    records: list[dict[str, str]] = []
    for record in verification_pool:
        direct_url, status, note = resolved.get(record["eprint_id"], ("", 0, "missing result"))
        if status != 200 or not direct_url or direct_url in existing_urls:
            record["resource_url"] = direct_url
            record["eprint_result"] = note
            continue
        record["resource_url"] = direct_url
        records.append(record)

    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(verify_pdf, record) for record in records]
        for future in as_completed(futures):
            eprint_id, status, content_type = future.result()
            statuses[eprint_id] = (status, content_type)

    verified = [
        record for record in records
        if statuses.get(record["eprint_id"], (0, ""))[0] == 200
        and "pdf" in statuses.get(record["eprint_id"], (0, ""))[1]
    ]
    track_rank = {"DM": 0, "EM": 1, "GA": 2}
    verified.sort(key=lambda item: (int(item["year"]), track_rank[item["track"]], item["course_title"], item["resource_url"]), reverse=True)
    print(f"Individually verified UTPedia target documents: {len(verified)}")
    selected = verified[:required]
    if len(selected) < required:
        raise RuntimeError(f"Only {len(selected)} individually verified UTPedia documents; refusing to pad Malaysia")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in selected:
            writer.writerow({
                "country": "Malaysia",
                "track": record["track"],
                "topic_tags": record["topic_tags"],
                "priority": "A",
                "source_type": "University past-examination archive",
                "source_title": "Universiti Teknologi PETRONAS UTPedia past examination questions",
                "source_url": record["source_url"],
                "resource_title": f"UTP Past Examination Question ({record['year']}) — {record['course_title']}",
                "resource_url": record["resource_url"],
                "resource_class": "University past examination question",
                "language": "English",
                "notes": f"Direct public PDF listed on the official UTPedia {record['year']} past-examination archive; classified as {record['family']}.",
                "access_model": "Free public download",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_ids = {record["eprint_id"] for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["eprint_id", "resource_url", "year", "course_title", "track", "eprint_result", "http_status", "content_type", "included"])
        for record in sorted(verification_pool, key=lambda item: int(item["eprint_id"])):
            status, content_type = statuses.get(record["eprint_id"], (0, "not verified"))
            writer.writerow([
                record["eprint_id"], record.get("resource_url", ""), record["year"], record["course_title"], record["track"],
                resolved.get(record["eprint_id"], ("", 0, "not fetched"))[2], status, content_type,
                "Yes" if record["eprint_id"] in selected_ids else "No",
            ])
    print(f"Wrote {len(selected)} verified Malaysia UTPedia records to {OUTPUT}")


if __name__ == "__main__":
    main()
