from __future__ import annotations

import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
SNAPSHOTS = Path("/home/ubuntu/malaysia_mco_html")
OUTPUT = DATA / "malaysia_mco_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_mco_url_audit.csv"
VERIFY_DATE = "2026-08-14"
ALLOWED_HOSTS = {"codeforces.com", "codechef.com", "discuss.codechef.com", "s3-ap-southeast-1.amazonaws.com", "ioimalaysia.org"}
PUBLISHED_URL_RE = re.compile(r"https?://[^\s\"<>]+")


def catalog_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle))
    return urls


def host_of(url: str) -> str:
    return re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/", 1)[0])


def allowed(url: str) -> bool:
    host = host_of(url)
    return host in ALLOWED_HOSTS and (
        re.fullmatch(r"https://codeforces\.com/group/[^/]+/contest/\d+", url)
        or re.fullmatch(r"https://codeforces\.com/gym/\d+", url)
        or re.fullmatch(r"https://www\.codechef\.com/[A-Za-z0-9]+", url)
        or re.fullmatch(r"https://discuss\.codechef\.com/questions/\d+/[a-z0-9-]+", url)
        or re.fullmatch(r'https://s3-ap-southeast-1\.amazonaws\.com/files\.ioimalaysia\.org/[^"\s]+\.(?:pdf|zip)', url)
        or re.fullmatch(r'https://ioimalaysia\.org/assets/files/[^"\s]+\.pdf', url)
    )


def clean_url(raw: str, base: str) -> str:
    return urljoin(base, raw.strip()).replace("&amp;", "&").rstrip(".,;)")


def discover(existing: set[str]) -> list[dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    snapshots = [*sorted(SNAPSHOTS.glob("20??.html")), SNAPSHOTS / "practice.html"]
    for path in snapshots:
        if not path.exists():
            continue
        year = path.stem
        source_url = (
            f"https://ioimalaysia.org/competition/mco/{year}/"
            if path.stem.isdigit()
            else "https://ioimalaysia.org/resource/for-student/practice/"
        )
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        published: list[tuple[str, str, str]] = [
            (
                clean_url(anchor["href"], source_url),
                " ".join(anchor.get_text(" ", strip=True).split()) or "Official linked resource",
                " ".join((anchor.find_previous(["h3", "h2"]).get_text(" ", strip=True) if anchor.find_previous(["h3", "h2"]) else path.stem).split()),
            )
            for anchor in soup.select("a[href]")
        ]
        published.extend((clean_url(raw, source_url), "Official archive-published resource URL", path.stem) for raw in PUBLISHED_URL_RE.findall(path.read_text(encoding="utf-8")))
        for resource_url, label, section in published:
            if not allowed(resource_url) or resource_url in existing:
                continue
            lower = f"{label} {resource_url}".lower()
            material = "Official editorial / solution" if "editorial" in lower else "Official contest resource"
            records[resource_url] = {
                "year": year,
                "source_url": source_url,
                "resource_url": resource_url,
                "label": label,
                "section": section,
                "material": material,
            }
    return sorted(records.values(), key=lambda item: (item["year"], item["resource_url"]), reverse=True)


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    result = subprocess.run(
        ["curl", "-L", "--silent", "--show-error", "--max-time", "20", "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}", record["resource_url"]],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = result.stdout.strip()
    if result.returncode != 0 or "|" not in output:
        return record["resource_url"], 0, "unavailable"
    code, content_type = output.split("|", 1)
    return record["resource_url"], int(code) if code.isdigit() else 0, content_type.lower() or "unknown"


def resource_class(record: dict[str, str]) -> str:
    url = record["resource_url"]
    if "editorial" in record["material"].lower():
        return "Official contest editorial / solution"
    if url.endswith(".pdf"):
        return "Official contest problem paper"
    if url.endswith(".zip"):
        return "Official contest test data"
    return "Official contest problem archive"


def main() -> None:
    candidates = discover(catalog_urls())
    print(f"Official MCO archive-linked non-duplicate candidates: {len(candidates)}")
    results: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(verify, candidate) for candidate in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            results[url] = (status, content_type)
    verified = [record for record in candidates if results.get(record["resource_url"], (0, ""))[0] == 200]
    print(f"Individually verified public MCO linked resources: {len(verified)}")

    fields = ["country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url", "resource_title", "resource_url", "resource_class", "language", "notes", "access_model", "verification_status", "free_resource"]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in verified:
            writer.writerow({
                "country": "Malaysia",
                "track": "DM",
                "topic_tags": "algorithms;competitive programming;discrete mathematics;contest",
                "priority": "A",
                "source_type": "Official competition archive",
                "source_title": "Malaysian Computing Olympiad annual archive",
                "source_url": record["source_url"],
                "resource_title": f"MCO {record['year']} — {record['section']} — {record['label']}",
                "resource_url": record["resource_url"],
                "resource_class": resource_class(record),
                "language": "English",
                "notes": f"Public {record['material'].lower()} explicitly linked from the official Malaysian Computing Olympiad {record['year']} archive page.",
                "access_model": "Free public web resource",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["year", "source_url", "resource_url", "source_label", "http_status", "content_type", "included"])
        for record in candidates:
            status, content_type = results.get(record["resource_url"], (0, "unavailable"))
            writer.writerow([record["year"], record["source_url"], record["resource_url"], record["label"], status, content_type, "Yes" if status == 200 else "No"])
    print(f"Wrote {len(verified)} Malaysia MCO records to {OUTPUT}")


if __name__ == "__main__":
    main()
