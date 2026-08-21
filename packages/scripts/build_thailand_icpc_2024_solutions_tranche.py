"""Verify and emit Chulalongkorn-hosted 2024 ICPC Thailand English solution PDFs.

Both resources are directly linked from the official Chulalongkorn 2024 past-
competitions page. The verifier requires direct public PDF access and extracted
English solution/problem evidence before producing catalog rows.
"""

from __future__ import annotations

import csv
import subprocess
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "apps/web/src/data/thailand_icpc_2024_solutions_verified_resources.csv"
AUDIT = ROOT / "research/thailand_icpc_2024_solutions_url_audit.csv"
SOURCE_URL = "https://icpc.cp.eng.chula.ac.th/2024/competitions"
FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title",
    "source_url", "resource_title", "resource_url", "resource_class", "language",
    "notes", "access_model", "verification_status", "free_resource",
]
CANDIDATES = [
    {
        "url": "https://icpc.cp.eng.chula.ac.th/2024/uploads/THA-NC-2024-Solutions.pdf",
        "title": "Thailand National Contest 2024 official English solutions",
        "source_title": "Chulalongkorn University — Thailand National Contest 2024",
    },
    {
        "url": "https://icpc.cp.eng.chula.ac.th/2024/uploads/ICPC-AsiaThailand2024-Solutions.pdf",
        "title": "ICPC Asia Thailand 2024 official English solutions",
        "source_title": "Chulalongkorn University — ICPC Asia Thailand 2024",
    },
]


def fetch_pdf(url: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SignalAtlasResearch/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.headers.get_content_type(), response.read()


def extract_text(pdf_bytes: bytes) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "solutions.pdf"
        text = Path(tmp) / "solutions.txt"
        pdf.write_bytes(pdf_bytes)
        subprocess.run(["pdftotext", "-f", "1", "-l", "20", str(pdf), str(text)], check=True, timeout=60)
        return text.read_text(errors="ignore")


def main() -> None:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    audit_rows: list[dict[str, object]] = []
    keep_rows: list[dict[str, str]] = []
    for candidate in CANDIDATES:
        try:
            status, content_type, body = fetch_pdf(candidate["url"])
            text = extract_text(body) if status == 200 and content_type == "application/pdf" else ""
            lower = text.lower()
            english_hits = sum(lower.count(token) for token in ("solution", "problem", "input", "output", "algorithm", "sample"))
            qualifies = status == 200 and content_type == "application/pdf" and "solution" in lower and "problem" in lower and english_hits >= 5
            evidence = "English solution and problem-statement evidence extracted" if qualifies else "Direct PDF or English substantive solution evidence insufficient"
        except Exception as exc:  # audit all candidates without promoting failures
            status, content_type, english_hits, qualifies, evidence = 0, "", 0, False, f"Fetch or extraction failed: {type(exc).__name__}"
        audit_rows.append({
            "resource_url": candidate["url"], "http_status": status, "content_type": content_type,
            "english_solution_hits": english_hits, "decision": "keep" if qualifies else "exclude", "evidence": evidence,
        })
        if qualifies:
            keep_rows.append({
                "country": "Thailand",
                "track": "DM",
                "topic_tags": "algorithms, data structures, graph theory, programming contest, solutions",
                "priority": "A",
                "source_type": "University contest organiser",
                "source_title": candidate["source_title"],
                "source_url": SOURCE_URL,
                "resource_title": candidate["title"],
                "resource_url": candidate["url"],
                "resource_class": "Solutions",
                "language": "English",
                "notes": "Direct public English solution PDF linked on Chulalongkorn University’s official 2024 competition archive; extracted text includes solution and problem evidence.",
                "access_model": "Free public PDF",
                "verification_status": "HTTP 200 · verified 2026-08-15",
                "free_resource": "yes",
            })
    with AUDIT.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["resource_url", "http_status", "content_type", "english_solution_hits", "decision", "evidence"])
        writer.writeheader()
        writer.writerows(audit_rows)
    with OUT.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(keep_rows)
    print(f"kept={len(keep_rows)}; audited={len(audit_rows)}")


if __name__ == "__main__":
    main()
