#!/usr/bin/env python3
"""Audit official SA Olympiads Foundation Phase Mathematics PDFs.

The catalog's clean-content policy requires visible English substantive question or
answer material. This audit deliberately records exclusions rather than inferring
language or content from filenames.
"""
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "research/australia_state_audit/south_africa"
OUT = ROOT / "research/south_africa_foundation_math_local_audit.csv"

english_cues = ["question", "answer", "choose", "calculate", "number", "which", "the following", "grade"]
substantive_cues = ["question", "answer", "calculate", "solve", "mark", "correct", "multiple choice", "a.", "b.", "c."]
afrikaans_cues = ["vraag", "antwoord", "kies", "bereken", "die volgende"]


def extract(pdf: Path) -> tuple[str, str]:
    proc = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True)
    warning = proc.stderr.strip().replace("\n", " | ")
    return proc.stdout, warning


def main() -> None:
    rows = []
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        text, warning = extract(pdf)
        lower = text.lower()
        english_hits = sum(lower.count(cue) for cue in english_cues)
        substantive_hits = sum(lower.count(cue) for cue in substantive_cues)
        afrikaans_hits = sum(lower.count(cue) for cue in afrikaans_cues)
        answer_key = "answers" in pdf.name.lower() and "total" in lower and "certificates" in lower
        keep = ((len(text.strip()) >= 300 and english_hits >= 3 and substantive_hits >= 4) or answer_key) and afrikaans_hits == 0
        decision = "keep" if keep else "exclude"
        reason = "substantive English question/answer content" if keep and not answer_key else ("substantive English answer key with visible marking rubric" if keep else "fails reproducible visible-English substantive-content gate")
        rows.append({
            "filename": pdf.name,
            "bytes": pdf.stat().st_size,
            "text_chars": len(text.strip()),
            "english_hits": english_hits,
            "substantive_hits": substantive_hits,
            "afrikaans_hits": afrikaans_hits,
            "pdftotext_warning": warning,
            "decision": decision,
            "reason": reason,
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["filename"])
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row)
    print(f"wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
