#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research" / "south_africa_junior_local_audit.csv"
OUT = ROOT / "client" / "src" / "data" / "south_africa_junior_math_verified_resources.csv"
CLEAN = ROOT / "research" / "clean_content_audit_south_africa_junior_math.csv"

BASE = {
    "country": "South Africa",
    "track": "GA",
    "topic_tags": "mathematics;olympiad;problem solving;multiple choice",
    "priority": "B",
    "source_type": "Official olympiad organizer",
    "source_title": "SA Olympiads Past Papers (official)",
    "source_url": "https://saolympiads.co.za/past-papers/",
    "language": "English",
    "access_model": "Free public web resource",
    "verification_status": "Official source HTTP 200 + local substantive audit · verified 2026-08-16",
    "free_resource": "Yes",
}

META = {
    "grade4_7_2017_questions.pdf": "South African Primary Mathematics Olympiads — Grade 4–7 Round 1 2017 Questions",
    "grade8_11_2017_questions.pdf": "Southern African Junior Mathematics Olympiad — Grade 8–11 Round 1 2017 Questions",
    "grade8_9_2021_questions.pdf": "Southern African Junior Mathematics Olympiad — Grades 8–9 2021 Questions",
}
URLS = {
    "grade4_7_2017_questions.pdf": "https://saolympiads.co.za/wp-content/uploads/2021/07/Grade-4-7-Round-1-2017-Questions.pdf",
    "grade8_11_2017_questions.pdf": "https://saolympiads.co.za/wp-content/uploads/2021/07/High-Grade-8-11-Round-1-2017-Questions.pdf",
    "grade8_9_2021_questions.pdf": "https://saolympiads.co.za/wp-content/uploads/2022/03/FEMSSISA-SA-MATHS-OLYMPIADS-GRADES-8-9-2021.pdf",
}

FIELDS = ["country","track","topic_tags","priority","source_type","source_title","source_url","resource_title","resource_url","resource_class","language","notes","access_model","verification_status","free_resource"]


def main() -> None:
    with AUDIT.open(encoding="utf-8", newline="") as f:
        audited = {row["file"]: row for row in csv.DictReader(f)}
    rows = []
    clean = []
    for filename, title in META.items():
        row = audited[filename]
        if row["decision"] != "keep":
            continue
        out = dict(BASE)
        out.update({
            "resource_title": title,
            "resource_url": URLS[filename],
            "resource_class": "Question paper",
            "notes": "Official public South African Olympiad PDF retained after local substantive English-content audit; direct question booklet contains visible mathematics problems and is catalogued as GA practice.",
        })
        rows.append(out)
        clean.append({"resource_url": URLS[filename], "local_file": filename, "decision": "keep", "text_chars": row["text_chars"], "english_cues": row["english_cues"], "substantive_cues": row["substantive_cues"], "reason": row["reason"]})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(rows)
    with CLEAN.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(clean[0]))
        writer.writeheader(); writer.writerows(clean)
    print(f"wrote {OUT} rows={len(rows)}")
    print(f"wrote {CLEAN} rows={len(clean)}")


if __name__ == "__main__":
    main()
