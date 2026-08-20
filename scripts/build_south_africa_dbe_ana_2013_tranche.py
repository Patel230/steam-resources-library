#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research" / "south_africa_dbe_ana_2013_local_audit.csv"
CLEAN = ROOT / "research" / "clean_content_pdf_audit_south_africa_dbe_ana_2013.csv"
OUT = ROOT / "client" / "src" / "data" / "south_africa_dbe_ana_2013_verified_resources.csv"
DOWNLOAD_DIR = ROOT / "research" / "downloads" / "south_africa_dbe_ana_2013"
HEADERS = {"User-Agent": "Mozilla/5.0 SignalAtlas official-source audit"}
FIELDS = ["country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url", "resource_title", "resource_url", "resource_class", "language", "notes", "access_model", "verification_status", "free_resource"]

CANDIDATES = [
    ("Grade 1 Mathematics English HL", "https://www.education.gov.za/LinkClick.aspx?fileticket=a8o12F67R5M%3d&tabid=600&portalid=0&mid=1811", "Question paper"),
    ("Grade 1 Mathematics English HL memo", "https://www.education.gov.za/LinkClick.aspx?fileticket=9fwvsPTPnmU%3d&tabid=600&portalid=0&mid=1811", "Marking memorandum"),
    ("Grade 2 English Mathematics HL", "https://www.education.gov.za/LinkClick.aspx?fileticket=eNx9l8cq57Y%3d&tabid=600&portalid=0&mid=1817", "Question paper"),
    ("Grade 2 English Mathematics HL memo", "https://www.education.gov.za/LinkClick.aspx?fileticket=FEiszSIXhTM%3d&tabid=600&portalid=0&mid=1817", "Marking memorandum"),
    ("Grade 3 Mathematics English HL", "https://www.education.gov.za/LinkClick.aspx?fileticket=c-eqzjWIClw%3d&tabid=600&portalid=0&mid=1825", "Question paper"),
    ("Grade 3 Mathematics English HL memo", "https://www.education.gov.za/LinkClick.aspx?fileticket=OgiWykWzJ4k%3d&tabid=600&portalid=0&mid=1825", "Marking memorandum"),
    ("Grade 4 English Mathematics", "https://www.education.gov.za/LinkClick.aspx?fileticket=uLLuSRQtEa8%3d&tabid=600&portalid=0&mid=1827", "Question paper"),
    ("Grade 4 English Mathematics memo", "https://www.education.gov.za/LinkClick.aspx?fileticket=pM9Qc-CgYEk%3d&tabid=600&portalid=0&mid=1827", "Marking memorandum"),
    ("Grade 5 Mathematics English", "https://www.education.gov.za/LinkClick.aspx?fileticket=N5xBnaOi038%3d&tabid=600&portalid=0&mid=1831", "Question paper"),
    ("Grade 5 Mathematics English memo", "https://www.education.gov.za/LinkClick.aspx?fileticket=vz4oBlg_sBM%3d&tabid=600&portalid=0&mid=1831", "Marking memorandum"),
    ("Grade 6 Mathematics English", "https://www.education.gov.za/LinkClick.aspx?fileticket=fNerpBPSdsY%3d&tabid=600&portalid=0&mid=1833", "Question paper"),
    ("Grade 6 Mathematics English memo", "https://www.education.gov.za/LinkClick.aspx?fileticket=rZzKX_FL2Jk%3d&tabid=600&portalid=0&mid=1833", "Marking memorandum"),
    ("Grade 9 Mathematics English", "https://www.education.gov.za/LinkClick.aspx?fileticket=_XzfD-d8gCA%3d&tabid=600&portalid=0&mid=1835", "Question paper"),
    ("Grade 9 Mathematics English memo", "https://www.education.gov.za/LinkClick.aspx?fileticket=aGVN5JvnBqM%3d&tabid=600&portalid=0&mid=1835", "Marking memorandum"),
]


def existing_urls() -> set[str]:
    found: set[str] = set()
    for path in (ROOT / "client" / "src" / "data").glob("*.csv"):
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                found.add(row.get("resource_url", "").strip())
    return found


def extract_text(path: Path) -> str:
    proc = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, timeout=35)
    return proc.stdout


def cues(text: str) -> tuple[int, int, int]:
    lower = f" {text.lower()} "
    english = sum(lower.count(token) for token in (" the ", " and ", " question", "answer", "mathematics", "grade", "marks"))
    substantive = sum(lower.count(token) for token in ("1.", "2.", "3.", "marks", "calculate", "determine", "solve", "answer"))
    non_english = sum(lower.count(token) for token in (" afrikaans", " vraestel", " tyd:", " waar ", " indien ", " isi "))
    return english, substantive, non_english


def main() -> None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    seen = existing_urls()
    audits: list[dict[str, str]] = []
    rows: list[dict[str, str]] = []
    clean: list[dict[str, str]] = []
    for label, url, resource_class in CANDIDATES:
        filename = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") + ".pdf"
        dest = DOWNLOAD_DIR / filename
        try:
            response = requests.get(url, headers=HEADERS, timeout=40, allow_redirects=True)
            dest.write_bytes(response.content)
            digest = hashlib.sha256(response.content).hexdigest()
            text = extract_text(dest) if response.status_code == 200 and response.content.startswith(b"%PDF") else ""
            english, substantive, non_english = cues(text)
            decision = "keep" if url not in seen and response.status_code == 200 and response.content.startswith(b"%PDF") and len(text) >= 500 and english >= 5 and substantive >= 4 and non_english == 0 else "exclude"
            reason = "Substantive English Mathematics question or memorandum" if decision == "keep" else f"Excluded by policy or audit: status={response.status_code}, pdf={response.content.startswith(b'%PDF')}, chars={len(text)}, english={english}, substantive={substantive}, non_english={non_english}, duplicate={url in seen}"
            audits.append({"label": label, "url": url, "decision": decision, "http_status": str(response.status_code), "local_file": filename, "text_chars": str(len(text)), "english_cues": str(english), "substantive_cues": str(substantive), "non_english_cues": str(non_english), "sha256": digest, "reason": reason})
            if decision == "keep":
                rows.append({
                    "country": "South Africa", "track": "GA/EM", "topic_tags": "mathematics;assessment;exam;questions;solutions", "priority": "A", "source_type": "Government education department", "source_title": "South African Department of Basic Education 2013 ANA tests and memos", "source_url": "https://www.education.gov.za/2013ANAtestsandmemos.aspx", "resource_title": f"South Africa 2013 ANA — {label}", "resource_url": url, "resource_class": resource_class, "language": "English", "notes": "Official public DBE 2013 Annual National Assessment Mathematics file labelled English; retained after substantive extracted-text audit and English-only visible-content review.", "access_model": "Free public web resource", "verification_status": "Official source HTTP 200 + local substantive audit · verified 2026-08-16", "free_resource": "Yes"
                })
                clean.append({"resource_url": url, "local_file": filename, "decision": "keep", "text_chars": str(len(text)), "english_cues": str(english), "substantive_cues": str(substantive), "reason": "Official DBE English Mathematics question/memorandum with substantive content and no detected non-English cues."})
        except Exception as exc:
            audits.append({"label": label, "url": url, "decision": "exclude", "http_status": "error", "local_file": filename, "text_chars": "0", "english_cues": "0", "substantive_cues": "0", "non_english_cues": "0", "sha256": "", "reason": f"audit error: {exc}"})
    with AUDIT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label", "url", "decision", "http_status", "local_file", "text_chars", "english_cues", "substantive_cues", "non_english_cues", "sha256", "reason"])
        writer.writeheader(); writer.writerows(audits)
    with CLEAN.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["resource_url", "local_file", "decision", "text_chars", "english_cues", "substantive_cues", "reason"])
        writer.writeheader(); writer.writerows(clean)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(rows)
    print(f"audited={len(audits)} kept={len(rows)} excluded={len(audits)-len(rows)} out={OUT}")
    for row in rows:
        print(row["resource_title"], row["resource_url"])


if __name__ == "__main__":
    main()

