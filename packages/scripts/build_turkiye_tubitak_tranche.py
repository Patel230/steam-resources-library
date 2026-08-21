from __future__ import annotations

import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
SOURCE_URL = "https://bilimolimpiyatlari.tubitak.gov.tr/tr/gecmis-sinav-sorulari"
SOURCE_SNAPSHOT = Path("/home/ubuntu/tubitak_turkiye_html/past_exam.html")
OUTPUT = DATA / "turkiye_tubitak_verified_resources.csv"
AUDIT = ROOT / "research/turkiye_tubitak_url_audit.csv"
VERIFY_DATE = "2026-08-14"

SUBJECTS = {
    "Matematik Dalı": ("Mathematics", "EM"),
    "Ortaokul Matematik Dalı": ("Middle School Mathematics", "EM"),
    "Bilgisayar Dalı": ("Computer Science", "DM"),
    "Ortaokul Bilgisayar Dalı": ("Middle School Computer Science", "DM"),
}

MATERIALS = {
    "Birinci Aşama Sınav Soruları ve Cevapları": "First-stage questions and answer key",
    "İkinci Aşama Sınav Soruları": "Second-stage questions",
    "Birinci Aşama Sınav Çözümleri": "First-stage official solutions",
    "İkinci Aşama Sınav Çözümleri": "Second-stage official solutions",
}


def classes(tag) -> set[str]:
    return set(tag.get("class", [])) if tag else set()


def existing_catalog() -> tuple[set[str], int]:
    urls: set[str] = set()
    turkiye_count = 0
    for path in DATA.glob("*.csv"):
        if path in {OUTPUT, DATA / "final_resources.csv"}:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = row.get("resource_url", "").strip()
                if url:
                    urls.add(url)
                if row.get("country") == "Türkiye" and row.get("free_resource", "").lower() == "yes":
                    turkiye_count += 1
    return urls, turkiye_count


def direct_col(row, column: str):
    for child in row.find_all("div", recursive=False):
        if column in classes(child):
            return child
    return None


def discover(existing_urls: set[str]) -> list[dict[str, str]]:
    if not SOURCE_SNAPSHOT.exists():
        raise RuntimeError(f"Missing official TÜBİTAK source snapshot: {SOURCE_SNAPSHOT}")
    soup = BeautifulSoup(SOURCE_SNAPSHOT.read_text(encoding="utf-8"), "html.parser")
    candidates: dict[str, dict[str, str]] = {}
    for section_id, section_kind in [("gecmis-sinav-sorulari", "questions"), ("gecmis-sinav-cozumleri", "solutions")]:
        section = soup.find("section", id=section_id)
        if not section:
            raise RuntimeError(f"Official archive section not found: {section_id}")
        for row in section.find_all("div", class_="row"):
            subject_col = direct_col(row, "col-md-3")
            if not subject_col:
                continue
            subject_turkish = subject_col.get_text(" ", strip=True)
            if subject_turkish not in SUBJECTS:
                continue
            subject, track = SUBJECTS[subject_turkish]
            content_col = direct_col(row, "col-md-9")
            if not content_col:
                raise RuntimeError(f"Missing official archive content column for {subject_turkish}")
            content_children = content_col.find_all("div", recursive=False)
            for index, material_col in enumerate(content_children):
                if "col-md-2" not in classes(material_col):
                    continue
                material_turkish = material_col.get_text(" ", strip=True)
                material = MATERIALS.get(material_turkish)
                if not material:
                    continue
                link_col = content_children[index + 1] if index + 1 < len(content_children) else None
                if not link_col or "col-md-4" not in classes(link_col):
                    raise RuntimeError(f"Unexpected source link-column structure for {subject_turkish}: {material_turkish}")
                for anchor in link_col.select("a[href]"):
                    url = anchor["href"].strip().replace("http://", "https://")
                    if not re.fullmatch(r"https://bilimolimpiyatlari\.tubitak\.gov\.tr/files/[A-Za-z0-9]+\.(?:pdf|zip)", url):
                        raise RuntimeError(f"Unexpected official TÜBİTAK file target: {url}")
                    year_label = anchor.get_text(" ", strip=True)
                    if not re.fullmatch(r"(?:Tüm Yıllar|\d{4}(?:-\d{4})?)", year_label):
                        raise RuntimeError(f"Missing source-published year label for {url}: {year_label}")
                    if url in existing_urls:
                        continue
                    record = {
                        "url": url,
                        "source_url": SOURCE_URL,
                        "subject": subject,
                        "track": track,
                        "material": material,
                        "year_label": year_label,
                        "section_kind": section_kind,
                    }
                    if url in candidates:
                        previous = candidates[url]
                        if previous != record:
                            raise RuntimeError(f"One official file is linked with conflicting archive metadata: {url}")
                    candidates[url] = record
    return list(candidates.values())


def verify(record: dict[str, str]) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "wget", "--server-response", "--spider", "--timeout=40", "--tries=1",
            "--user-agent=Signal Atlas catalog verifier/1.0", record["url"],
        ],
        capture_output=True,
        text=True,
        timeout=55,
        check=False,
    )
    transcript = f"{result.stdout}\n{result.stderr}"
    statuses = re.findall(r"HTTP/\S+\s+(\d{3})", transcript)
    content_types = re.findall(r"Content-Type:\s*([^\r\n;]+)", transcript, flags=re.IGNORECASE)
    return record["url"], int(statuses[-1]) if statuses else 0, content_types[-1].lower() if content_types else "unknown"


def year_key(label: str) -> int:
    years = re.findall(r"\d{4}", label)
    return int(years[-1]) if years else 0


def main() -> None:
    existing_urls, baseline = existing_catalog()
    required = max(0, 100 - baseline)
    candidates = discover(existing_urls)
    print(f"Türkiye baseline: {baseline}; target additions: {required}; official TÜBİTAK candidates: {len(candidates)}")
    if len(candidates) < required:
        raise RuntimeError("Official TÜBİTAK archive capacity is below the target; refusing to pad Türkiye")

    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(verify, record) for record in candidates]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)

    verified = [
        record for record in candidates
        if statuses.get(record["url"], (0, ""))[0] == 200
        and any(kind in statuses.get(record["url"], (0, ""))[1] for kind in ["pdf", "zip", "octet-stream"])
    ]
    track_rank = {"DM": 1, "EM": 0}
    verified.sort(
        key=lambda record: (year_key(record["year_label"]), track_rank[record["track"]], record["section_kind"], record["subject"], record["url"]),
        reverse=True,
    )
    print(f"Individually verified public TÜBİTAK resources: {len(verified)}")
    selected = verified[:required]
    if len(selected) < required:
        raise RuntimeError(f"Only {len(selected)} verified TÜBİTAK resources; refusing to pad Türkiye")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in selected:
            is_solution = "solutions" in record["material"].lower()
            writer.writerow({
                "country": "Türkiye",
                "track": record["track"],
                "topic_tags": "mathematical olympiad;geometry;contest;past paper;questions;solutions" if record["track"] == "EM" else "discrete mathematics;informatics;algorithms;programming;olympiad;contest;past paper;solutions",
                "priority": "A",
                "source_type": "National science Olympiad archive",
                "source_title": "TÜBİTAK National Science Olympiads past questions and solutions",
                "source_url": record["source_url"],
                "resource_title": f"TÜBİTAK National {record['subject']} Olympiad — {record['material']} — {record['year_label']}",
                "resource_url": record["url"],
                "resource_class": "Official Olympiad solutions" if is_solution else "Past Olympiad questions and answer key",
                "language": "Turkish source; English catalog title",
                "notes": "Direct public file listed in the official TÜBİTAK National Science Olympiads archive.",
                "access_model": "Free public download",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    selected_urls = {record["url"] for record in selected}
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "subject", "material", "year_label", "section", "http_status", "content_type", "included"])
        for record in sorted(candidates, key=lambda item: item["url"]):
            status, content_type = statuses.get(record["url"], (0, "not verified"))
            writer.writerow([record["url"], record["subject"], record["material"], record["year_label"], record["section_kind"], status, content_type, "Yes" if record["url"] in selected_urls else "No"])
    print(f"Wrote {len(selected)} verified TÜBİTAK records to {OUTPUT}")


if __name__ == "__main__":
    main()
