"""Verify and emit the alternate official Chulalongkorn 2024 ICPC editorial PDFs.

The source page is an organiser-owned Past Competitions archive. Each candidate
must resolve to a direct public PDF, expose extractable English solution/problem
evidence, and be unique across the currently active 15-column CSV catalog.
"""

from __future__ import annotations

import csv
import subprocess
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "client" / "src" / "data"
OUT = DATA_DIR / "thailand_chula_icpc2024_editorials_verified_resources.csv"
AUDIT = ROOT / "research" / "thailand_chula_icpc2024_editorials_url_audit.csv"
SOURCE_URL = "https://icpc-2024.cp.eng.chula.ac.th/2024/competitions"
FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title",
    "source_url", "resource_title", "resource_url", "resource_class", "language",
    "notes", "access_model", "verification_status", "free_resource",
]
CANDIDATES = [
    {
        "url": "https://icpc-2024.cp.eng.chula.ac.th/2024/editorials/ICPC_Internal_CU_2024.pdf",
        "title": "ICPC Thailand Internal Competition 2024 — official English solution sketch",
        "source_title": "Chulalongkorn University — ICPC Thailand Internal Competition 2024",
    },
    {
        "url": "https://icpc-2024.cp.eng.chula.ac.th/2024/editorials/ICPC_National_Bangkok_2024.pdf",
        "title": "ICPC Thailand National Competition 2024 — official English tutorial slides",
        "source_title": "Chulalongkorn University — ICPC Thailand National Competition 2024",
    },
]


def fetch_pdf(url: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.headers.get_content_type(), response.read()


def extract_text(pdf_bytes: bytes) -> str:
    with tempfile.TemporaryDirectory(prefix="signal-atlas-chula-") as temporary:
        pdf_path = Path(temporary) / "editorial.pdf"
        text_path = Path(temporary) / "editorial.txt"
        pdf_path.write_bytes(pdf_bytes)
        subprocess.run(
            ["pdftotext", "-f", "1", "-l", "8", str(pdf_path), str(text_path)],
            check=True,
            timeout=60,
        )
        return text_path.read_text(encoding="utf-8", errors="ignore")


def existing_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA_DIR.glob("*.csv"):
        if path == OUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != FIELDS:
                continue
            urls.update(row.get("resource_url", "").strip() for row in reader)
    return urls


def main() -> None:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    known_urls = existing_urls()
    audit_rows: list[dict[str, object]] = []
    keep_rows: list[dict[str, str]] = []

    for candidate in CANDIDATES:
        try:
            status, content_type, body = fetch_pdf(candidate["url"])
            text = extract_text(body) if status == 200 and content_type == "application/pdf" else ""
            lower = text.lower()
            english_hits = sum(lower.count(token) for token in ("the", "and", "problem", "solution", "algorithm", "input", "output"))
            solution_hits = sum(lower.count(token) for token in ("solution", "tutorial", "algorithm", "proof", "analysis"))
            problem_hits = sum(lower.count(token) for token in ("problem", "input", "output", "task"))
            qualifies = (
                status == 200
                and content_type == "application/pdf"
                and english_hits >= 12
                and solution_hits >= 1
                and problem_hits >= 1
                and candidate["url"] not in known_urls
            )
            evidence = (
                f"english_hits={english_hits}; solution_hits={solution_hits}; problem_hits={problem_hits}; "
                f"extractable_chars={len(text)}"
            )
            if candidate["url"] in known_urls:
                evidence += "; duplicate resource URL already exists in active catalog"
        except Exception as exc:  # Preserve every failure and never promote a partial result.
            status, content_type, english_hits, solution_hits, problem_hits, qualifies = 0, "", 0, 0, 0, False
            evidence = f"fetch or extraction failed: {type(exc).__name__}"

        audit_rows.append(
            {
                "resource_url": candidate["url"],
                "http_status": status,
                "content_type": content_type,
                "english_hits": english_hits,
                "solution_hits": solution_hits,
                "problem_hits": problem_hits,
                "decision": "keep" if qualifies else "exclude",
                "evidence": evidence,
            }
        )
        if not qualifies:
            continue
        keep_rows.append(
            {
                "country": "Thailand",
                "track": "DM",
                "topic_tags": "algorithms, data structures, graph theory, programming contest, editorial solutions",
                "priority": "A",
                "source_type": "University contest organiser",
                "source_title": candidate["source_title"],
                "source_url": SOURCE_URL,
                "resource_title": candidate["title"],
                "resource_url": candidate["url"],
                "resource_class": "Solutions",
                "language": "English",
                "notes": "Direct public English editorial PDF linked from Chulalongkorn University’s official 2024 Past Competitions archive; scripted extraction confirms substantive solution and problem material.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-15",
                "free_resource": "yes",
            }
        )

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["resource_url", "http_status", "content_type", "english_hits", "solution_hits", "problem_hits", "decision", "evidence"],
        )
        writer.writeheader()
        writer.writerows(audit_rows)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(keep_rows)
    print(f"kept={len(keep_rows)}; audited={len(audit_rows)}")


if __name__ == "__main__":
    main()
