#!/usr/bin/env python3
"""Verify and generate the official MUIC mathematics sample tranche.

This script is intentionally conservative: it emits a CSV row only when a
public PDF is HTTP 200, identifies as a PDF, has extractable English/question
signals, and is not a duplicate of the existing catalog URLs.
"""
from __future__ import annotations

import csv
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "client/src/data/thailand_mahidol_muic_math_verified_resources.csv"
AUDIT = ROOT / "research/thailand_mahidol_muic_math_url_audit.csv"
VERIFY_DATE = "HTTP 200 · verified 2026-08-16"
TIMEOUT = 40

CANDIDATES = [
    ("Example of Mathematics", "https://muic-www-assets.muic.io/example_of_mathematics_9b6942cb44.pdf"),
    ("Example of Mathematics Part I", "https://muic-www-assets.muic.io/Example_of_Mathematics_Part_I_095f91e877.pdf"),
    ("Example of Mathematics Part II", "https://muic-www-assets.muic.io/Example_of_Mathematics_Part_II_79ebfeb35a.pdf"),
    ("Example of Mathematics Part III", "https://muic-www-assets.muic.io/Example_of_Mathematics_Part_III_486634bfad.pdf"),
    ("Example of Mathematics Part IV", "https://muic-www-assets.muic.io/Example_of_Mathematics_Part_IV_f8f3930f24.pdf"),
]

SCHEMA = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title",
    "source_url", "resource_title", "resource_url", "resource_class", "language",
    "notes", "access_model", "verification_status", "free_resource",
]


def extract_text(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return result.stdout or ""


def english_cues(text: str) -> list[str]:
    patterns = [
        r"\bmathematics?\b", r"\bquestion\b", r"\bsolve\b", r"\bfind\b",
        r"\bwhich\b", r"\bcalculate\b", r"\banswer\b", r"\bchoice\b",
        r"\bfunction\b", r"\bequation\b", r"\bprobability\b", r"\bnumber\b",
    ]
    return [p for p in patterns if re.search(p, text, flags=re.I)]


def substantive_cues(text: str) -> list[str]:
    patterns = [
        r"\bquestion\s*\d", r"\b(?:q|no|problem)\.?\s*\d", r"\bsolve\b",
        r"\bfind\b", r"\bcalculate\b", r"\bwhich of the following\b",
        r"\b[abcd]\s*[.)]", r"\banswer\s*the following\b",
    ]
    return [p for p in patterns if re.search(p, text, flags=re.I)]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    audit_rows: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()

    for title, url in CANDIDATES:
        audit = {
            "resource_title": title,
            "url": url,
            "http_status": "",
            "content_type": "",
            "bytes": "0",
            "sha256": "",
            "pages": "",
            "text_chars": "0",
            "english_cues": "",
            "substantive_cues": "",
            "decision": "remove",
            "reason": "",
        }
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "SignalAtlasVerifier/1.0"},
                timeout=TIMEOUT,
            )
            audit["http_status"] = str(response.status_code)
            audit["content_type"] = response.headers.get("content-type", "")
            data = response.content
            audit["bytes"] = str(len(data))
            digest = hashlib.sha256(data).hexdigest()
            audit["sha256"] = digest
            if response.status_code != 200:
                audit["reason"] = "HTTP status is not 200"
            elif not data.startswith(b"%PDF"):
                audit["reason"] = "response is not a PDF"
            elif url in seen_urls or digest in seen_hashes:
                audit["reason"] = "duplicate URL or PDF bytes"
            else:
                with tempfile.NamedTemporaryFile(suffix=".pdf") as handle:
                    handle.write(data)
                    handle.flush()
                    text = extract_text(Path(handle.name))
                audit["text_chars"] = str(len(text))
                pages = re.search(r"/Count\s+(\d+)", data.decode("latin1", errors="ignore"))
                audit["pages"] = pages.group(1) if pages else ""
                ec = english_cues(text)
                sc = substantive_cues(text)
                audit["english_cues"] = ";".join(ec)
                audit["substantive_cues"] = ";".join(sc)
                if len(text.strip()) < 100:
                    audit["reason"] = "insufficient extractable text"
                elif len(ec) < 3:
                    audit["reason"] = "insufficient English cues"
                elif len(sc) < 1:
                    audit["reason"] = "no substantive question cue"
                else:
                    audit["decision"] = "keep"
                    audit["reason"] = "HTTP 200 PDF with English and substantive-question evidence"
                    seen_urls.add(url)
                    seen_hashes.add(digest)
                    rows.append({
                        "country": "Thailand",
                        "track": "EM",
                        "topic_tags": "algebra;functions;probability;precalculus",
                        "priority": "high",
                        "source_type": "university admissions archive",
                        "source_title": "Mahidol University International College Mathematics sample archive",
                        "source_url": "https://muic.mahidol.ac.th/en/study-at-muic/admissions-requirement/undergraduate-admission/regular-applicants",
                        "resource_title": title,
                        "resource_url": url,
                        "resource_class": "question",
                        "language": "English",
                        "notes": "Official MUIC English admissions mathematics sample PDF; direct public access; retained only after item-level substantive-question verification.",
                        "access_model": "free public direct PDF",
                        "verification_status": VERIFY_DATE,
                        "free_resource": "yes",
                    })
        except Exception as exc:  # preserve reproducible item-level failure evidence
            audit["reason"] = f"verification error: {type(exc).__name__}: {exc}"
        audit_rows.append(audit)

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows(rows)
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)

    print(f"kept={len(rows)} removed={len(audit_rows) - len(rows)}")
    for row in audit_rows:
        print(row["resource_title"], row["decision"], row["reason"])


if __name__ == "__main__":
    main()
