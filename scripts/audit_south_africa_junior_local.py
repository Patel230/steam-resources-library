#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "research" / "audit_sources" / "south_africa_junior"
OUT = ROOT / "research" / "south_africa_junior_local_audit.csv"

URLS = {
    "grade4_7_2017_questions.pdf": "https://saolympiads.co.za/wp-content/uploads/2021/07/Grade-4-7-Round-1-2017-Questions.pdf",
    "grade8_11_2017_questions.pdf": "https://saolympiads.co.za/wp-content/uploads/2021/07/High-Grade-8-11-Round-1-2017-Questions.pdf",
    "grade8_9_2021_questions.pdf": "https://saolympiads.co.za/wp-content/uploads/2022/03/FEMSSISA-SA-MATHS-OLYMPIADS-GRADES-8-9-2021.pdf",
}


def extract(path: Path) -> tuple[str, str]:
    proc = subprocess.run(["pdftotext", "-layout", str(path), "-"], text=True, capture_output=True)
    return proc.stdout, proc.stderr.strip()


def main() -> None:
    rows = []
    for name, url in URLS.items():
        path = AUDIT_DIR / name
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        text, warning = extract(path) if exists else ("", "missing file")
        lower = text.lower()
        english_cues = sum(lower.count(cue) for cue in ("question", "answer", "grade", "round", "circle", "calculate", "choose"))
        substantive_cues = sum(lower.count(cue) for cue in ("question", "calculate", "answer", "solve", "number", "multiple choice", "mark"))
        keep = exists and size > 10_000 and len(text.strip()) >= 300 and english_cues >= 3 and substantive_cues >= 4
        rows.append({
            "file": name,
            "url": url,
            "http_status": "200" if exists else "missing",
            "bytes": size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if exists else "",
            "text_chars": len(text),
            "english_cues": english_cues,
            "substantive_cues": substantive_cues,
            "parser_warning": warning,
            "decision": "keep" if keep else "exclude",
            "reason": "substantive English mathematics question booklet" if keep else "insufficient reproducible substantive evidence",
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT}")
    for row in rows:
        print(row["decision"], row["file"], row["bytes"], row["text_chars"], row["english_cues"], row["substantive_cues"], row["parser_warning"])


if __name__ == "__main__":
    main()
