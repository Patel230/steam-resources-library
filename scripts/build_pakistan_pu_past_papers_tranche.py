from __future__ import annotations

import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "client/src/data"
SOURCE_DIR = Path("/home/ubuntu/pu_pakistan_html/sources")
OUTPUT = DATA / "pakistan_pu_verified_resources.csv"
AUDIT = ROOT / "research/pakistan_pu_url_audit.csv"
MATH_SOURCE_URLS = {
    "mathematics_combination_i.md": "https://pu.edu.pk/home/bs4yearsdegree/BS-4Years-Mathematics1.html",
    "mathematics_combination_ii.md": "https://pu.edu.pk/home/bs4yearsdegree/BS-4Years-Mathematics2.html",
}
CS_SOURCE_URL = "https://pu.edu.pk/page/show/Past-Papers-BS-Computer-Science.html"
VERIFY_DATE = "2026-08-14"


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    pakistan_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
                if row.get("country") == "Pakistan" and row.get("free_resource") == "Yes":
                    pakistan_count += 1
    return urls, pakistan_count


def course_track(course: str) -> str | None:
    normalized = course.lower()
    if any(token in normalized for token in ["islam", "pakistan studies", "sociology", "physics"]):
        return None
    if "english" in normalized:
        return "GA"
    if any(token in normalized for token in ["discrete", "graph", "group theory", "ring", "set theory", "number theory", "module", "computer"]):
        return "DM"
    if any(token in normalized for token in [
        "mathematics", "calculus", "vectors", "mechanics", "statistics", "linear algebra", "ordinary differential",
        "partial differential", "analysis", "topology", "geometry", "operations research", "numerical", "tensor",
        "approximation", "fluid", "measure theory", "mathematical physics",
    ]):
        return "EM"
    raise RuntimeError(f"Unclassified source-published University of the Punjab course: {course}")


def discover_math(existing_urls: set[str]) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for filename, source_url in MATH_SOURCE_URLS.items():
        path = SOURCE_DIR / filename
        if not path.exists():
            raise RuntimeError(f"Missing official source snapshot: {path}")
        for line in path.read_text(encoding="utf-8").splitlines():
            if "Past-Papers/Math" not in line:
                continue
            parts = line.split("|")
            if len(parts) < 4:
                raise RuntimeError(f"Unexpected official table row shape: {line}")
            course = re.sub(r"\*", "", parts[1]).strip()
            track = course_track(course)
            for label, url in re.findall(r"\[([^\]]+)\]\((https://pu\.edu\.pk/downloads/BS-4Years/Past-Papers/Math[^)]+\.pdf)\)", line):
                if not re.fullmatch(r"20\d{2}", label):
                    raise RuntimeError(f"Missing source-published year label: {url}")
                if track is None or url in existing_urls:
                    continue
                existing = records.get(url)
                current = {
                    "url": url,
                    "year": label,
                    "course": course,
                    "track": track,
                    "source_url": source_url,
                    "source_label": f"{course} — {label}",
                }
                if existing and existing["course"] != course:
                    raise RuntimeError(f"One published paper URL is assigned to multiple courses: {url}")
                records[url] = current
    return records


def discover_cs(existing_urls: set[str]) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    entries = [
        ("B.S. in Computer Science First Year Annual 2022", "2022", "https://pu.edu.pk/downloads/Past-Papers/BS-Computer-Science-1st-Year-a22.pdf"),
        ("B.S. in Computer Science Second Year Annual 2022", "2022", "https://pu.edu.pk/downloads/Past-Papers/BS-Computer-Science-2nd-Year-a22.pdf"),
        ("B.S. in Computer Science Third Year Annual 2021", "2021", "https://pu.edu.pk/downloads/Past-Papers/BS-Computer-Science-3rd-Year-a22.pdf"),
        ("B.S. in Computer Science Fourth Year Annual 2021", "2021", "https://pu.edu.pk/downloads/Past-Papers/BS-Computer-Science-4th-Year-a22.pdf"),
        ("B.S. in Computer Science First Year Annual 2021", "2021", "https://pu.edu.pk/downloads/Past-Papers/BS-Computer-Science-1st-Year-a21.pdf"),
        ("B.S. in Computer Science Second Year Annual 2021", "2021", "https://pu.edu.pk/downloads/Past-Papers/BS-Computer-Science-2nd-Year-a21.pdf"),
        ("B.S. in Computer Science Third Year Annual 2021", "2021", "https://pu.edu.pk/downloads/Past-Papers/BS-Computer-Science-3rd-Year-a21.pdf"),
        ("B.S. in Computer Science Fourth Year Annual 2021", "2021", "https://pu.edu.pk/downloads/Past-Papers/BS-Computer-Science-4th-Year-a21.pdf"),
    ]
    for title, year, url in entries:
        if url in existing_urls:
            continue
        records[url] = {
            "url": url,
            "year": year,
            "course": title,
            "track": "DM",
            "source_url": CS_SOURCE_URL,
            "source_label": title,
        }
    return records


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "wget", "--server-response", "--spider", "--timeout=35", "--tries=1",
            "--user-agent=Signal Atlas catalog verifier/1.0", record["url"],
        ],
        capture_output=True,
        text=True,
        timeout=50,
        check=False,
    )
    transcript = f"{result.stdout}\n{result.stderr}"
    codes = re.findall(r"HTTP/\S+\s+(\d{3})", transcript)
    types = re.findall(r"Content-Type:\s*([^\r\n;]+)", transcript, flags=re.IGNORECASE)
    status = int(codes[-1]) if codes else 0
    content_type = types[-1].lower() if types else "unknown"
    return record["url"], status, content_type


def main() -> None:
    existing_urls, baseline = existing_catalog()
    required = max(0, 100 - baseline)
    candidates_by_url = discover_math(existing_urls)
    for url, record in discover_cs(existing_urls).items():
        if url in candidates_by_url:
            raise RuntimeError(f"Duplicate direct URL across official Pakistan source pages: {url}")
        candidates_by_url[url] = record
    candidates = list(candidates_by_url.values())
    print(f"Pakistan baseline: {baseline}; target additions: {required}; University of the Punjab non-duplicate candidates: {len(candidates)}")
    if len(candidates) < required:
        raise RuntimeError("Official source inventory is below the required target; refusing to pad Pakistan’s tranche")

    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(verify, candidate) for candidate in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)

    verified = [
        record for record in candidates
        if statuses.get(record["url"], (0, ""))[0] == 200
        and "pdf" in statuses.get(record["url"], (0, ""))[1]
    ]
    track_rank = {"DM": 2, "EM": 1, "GA": 0}
    verified.sort(
        key=lambda record: (int(record["year"]), track_rank[record["track"]], record["course"], record["url"]),
        reverse=True,
    )
    print(f"University of the Punjab individually verified public PDFs: {len(verified)}")
    selected = verified[:required]
    if len(selected) < required:
        raise RuntimeError(f"Only {len(selected)} individually verified Pakistan PDFs; refusing to pad the country target")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in selected:
            tags = {
                "GA": "general aptitude;English;communication;exam;past paper",
                "EM": "engineering mathematics;calculus;linear algebra;statistics;analysis;mathematical methods;exam;past paper",
                "DM": "discrete mathematics;computer science;algorithms;logic;graph theory;algebra;exam;past paper",
            }[record["track"]]
            writer.writerow({
                "country": "Pakistan",
                "track": record["track"],
                "topic_tags": tags,
                "priority": "A",
                "source_type": "University past-paper archive",
                "source_title": "University of the Punjab mathematics and computer science past papers",
                "source_url": record["source_url"],
                "resource_title": f"University of the Punjab {record['course']} past examination — {record['year']}",
                "resource_url": record["url"],
                "resource_class": "Past exam paper",
                "language": "English",
                "notes": "Direct public PDF listed in the University of the Punjab official past-paper archive.",
                "access_model": "Free public PDF",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {record["url"] for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "source_url", "source_label", "track", "http_status", "content_type", "included"])
        for record in sorted(candidates, key=lambda item: item["url"]):
            status, content_type = statuses.get(record["url"], (0, "not verified"))
            writer.writerow([
                record["url"], record["source_url"], record["source_label"], record["track"], status, content_type,
                "Yes" if record["url"] in selected_urls else "No",
            ])
    print(f"Wrote {len(selected)} verified University of the Punjab records to {OUTPUT}")


if __name__ == "__main__":
    main()
