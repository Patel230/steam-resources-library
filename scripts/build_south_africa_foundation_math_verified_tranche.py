#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research/south_africa_foundation_math_local_audit.csv"
OUT = ROOT / "client/src/data/south_africa_foundation_math_verified_resources.csv"
MANIFEST = ROOT / "research/clean_content_document_audit_south_africa_foundation_math.csv"
SOURCE = "https://saolympiads.co.za/past-papers/"
BASE = "https://saolympiads.co.za/wp-content/uploads/"

URLS = {
    "TIAMSE-NATIONAL-FOUNDATION-PHASE-MATHEMATICS-OLYMPIADS-GRADES-1-3.pdf": BASE + "2022/03/TIAMSE-NATIONAL-FOUNDATION-PHASE-MATHEMATICS-OLYMPIADS-GRADES-1-3.pdf",
    "FEMSSISA-MATHEMATICS-OLYMPIAD-ANSWERS-GR-1-3-2022.pdf": BASE + "2022/12/FEMSSISA-MATHEMATICS-OLYMPIAD-ANSWERS-GR-1-3-2022.pdf",
    "FEMSSISA-Grade-1-Mathematics-Olympiads-2022.pdf": BASE + "2022/12/FEMSSISA-Grade-1-Mathematics-Olympiads-2022.pdf",
    "FOUNDATION-PHASE-MATHEMATICS-OLYMPIAD-ANSWERS-GR-1-3-2023.pdf": BASE + "2023/12/FOUNDATION-PHASE-MATHEMATICS-OLYMPIAD-ANSWERS-GR-1-3-2023.pdf",
    "FEMSSISA-Grade-1-Mathematics-Olympiads-2023.pdf": BASE + "2023/12/FEMSSISA-Grade-1-Mathematics-Olympiads-2023.pdf",
    "FOUNDATION-PHASE-MATHEMATICS-OLYMPIAD-ANSWERS-GR-1-3-2024.pdf": BASE + "2025/01/FOUNDATION-PHASE-MATHEMATICS-OLYMPIAD-ANSWERS-GR-1-3-2024.pdf",
    "FEMSSISA-Grade-1-Mathematics-Olympiads-2024.pdf": BASE + "2025/01/FEMSSISA-Grade-1-Mathematics-Olympiads-2024.pdf",
    "FOUNDATION-PHASE-MATHEMATICS-OLYMPIAD-ANSWERS-GR-1-3-2025.pdf": BASE + "2025/11/FOUNDATION-PHASE-MATHEMATICS-OLYMPIAD-ANSWERS-GR-1-3-2025.pdf",
    "FEMSSISA-Grade-1-Mathematics-Olympiads-2025.pdf": BASE + "2025/11/FEMSSISA-Grade-1-Mathematics-Olympiads-2025.pdf",
}


def title(filename: str) -> str:
    stem = filename.removesuffix(".pdf").replace("-", " ")
    return "South African Foundation Phase Mathematics Olympiad — " + stem.replace("FEMSSISA ", "")


def main() -> None:
    rows = []
    audits = []
    with AUDIT.open(encoding="utf-8", newline="") as fh:
        for audit in csv.DictReader(fh):
            if audit["decision"] != "keep":
                continue
            filename = audit["filename"]
            if filename not in URLS:
                raise SystemExit(f"missing URL mapping: {filename}")
            is_answer = "answers" in filename.lower()
            rows.append({
                "country": "South Africa",
                "track": "GA",
                "topic_tags": "mathematics;olympiad;problem solving;multiple choice;answers" if is_answer else "mathematics;olympiad;problem solving;multiple choice",
                "priority": "B",
                "source_type": "Official olympiad organizer",
                "source_title": "SA Olympiads Past Papers (official)",
                "source_url": SOURCE,
                "resource_title": title(filename),
                "resource_url": URLS[filename],
                "resource_class": "Solution key" if is_answer else "Question paper",
                "language": "English",
                "notes": "Official public South African Foundation Phase Mathematics Olympiad PDF retained after local substantive English-content audit; primary-level mathematics is catalogued as GA practice, with no language inference from filename.",
                "access_model": "Free public web resource",
                "verification_status": "Official source HTTP 200 + local substantive audit · verified 2026-08-16",
                "free_resource": "Yes",
            })
            audits.append({"filename": filename, "resource_url": URLS[filename], "decision": "keep", "text_chars": audit["text_chars"], "reason": audit["reason"], "pdftotext_warning": audit["pdftotext_warning"]})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    with MANIFEST.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(audits[0]))
        writer.writeheader(); writer.writerows(audits)
    print(json.dumps({"rows": len(rows), "csv": str(OUT), "audit": str(MANIFEST)}, indent=2))


if __name__ == "__main__":
    main()
