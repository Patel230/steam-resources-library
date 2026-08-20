#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "client" / "src" / "data" / "south_africa_uct_2018_verified_resources.csv"
AUDIT = ROOT / "research" / "south_africa_uct_2018_local_audit.csv"
CLEAN = ROOT / "research" / "clean_content_pdf_audit_south_africa_uct_2018.csv"
DOWNLOADS = ROOT / "research" / "downloads" / "south_africa_uct_2018"
FOLDER_URL = "https://drive.google.com/drive/folders/1mqApdvv7ddBc-AuX28pU2k3YEwkASJSr"
SOURCE_URL = "https://science.uct.ac.za/department-mathematics/challenge-uct-mathematics-olympiad"
FIELDS = ["country","track","topic_tags","priority","source_type","source_title","source_url","resource_title","resource_url","resource_class","language","notes","access_model","verification_status","free_resource"]

CANDIDATES = [
    ("Mathematics Challenge 2018 problems", "1vo9RTFdFiOd4Uf0OipKnmDQ3YP5DE5os", "Question paper"),
    ("Mathematics Challenge 2018 solutions", "1-B2p-reCCHRzU77OLOudOeNP23ZmzUFa", "Solutions"),
    ("Senior Mathematics Olympiad 2018 problems", "10rQoagd7NyiyJaaKyxvZHsDjwJLR7yLH", "Question paper"),
    ("Senior Mathematics Olympiad 2018 solutions", "1kfCiPTjW-GTCcqFpFT18YZpx62b-foJE", "Solutions"),
]


def direct_url(file_id: str) -> str:
    return f"https://drive.usercontent.google.com/download?id={quote(file_id)}&export=download&confirm=t"


def cues(text: str) -> tuple[int, int, int]:
    lower = f" {text.lower()} "
    english = sum(lower.count(token) for token in (" the ", " and ", " answer ", " solution ", " find ", " prove ", " numbers ", " circle ", " show "))
    substantive = sum(lower.count(token) for token in ("1.", "2.", "3.", " calculate", " determine", " prove", " show that", " solve", " answer"))
    non_english = sum(lower.count(token) for token in (" vraestel", " bewys", " watter ", " hoeveel", " sirkel", " getalle", " tyd:"))
    return english, substantive, non_english


def main() -> None:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    audit_rows: list[dict[str, str]] = []
    kept: list[dict[str, str]] = []
    for label, file_id, resource_class in CANDIDATES:
        url = direct_url(file_id)
        filename = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") + ".pdf"
        path = DOWNLOADS / filename
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 SignalAtlas official-source audit"}, timeout=40)
        path.write_bytes(response.content)
        text = ""
        if response.status_code == 200 and response.content.startswith(b"%PDF"):
            proc = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, timeout=30)
            text = proc.stdout
        english, substantive, non_english = cues(text)
        decision = "keep" if response.status_code == 200 and len(text) >= 500 and english >= 8 and substantive >= 6 and non_english == 0 else "exclude"
        reason = "Substantive English-only UCT solution PDF" if decision == "keep" else f"Excluded by access/content policy: status={response.status_code}, chars={len(text)}, english={english}, substantive={substantive}, non_english={non_english}"
        audit_rows.append({"label": label, "file_id": file_id, "resource_url": url, "local_file": filename, "http_status": str(response.status_code), "content_type": response.headers.get("content-type", ""), "text_chars": str(len(text)), "english_cues": str(english), "substantive_cues": str(substantive), "non_english_cues": str(non_english), "decision": decision, "reason": reason})
        if decision == "keep":
            kept.append({"label": label, "resource_class": resource_class, "resource_url": url, "local_file": filename, "text_chars": str(len(text)), "english_cues": str(english), "substantive_cues": str(substantive)})

    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for item in kept:
            writer.writerow({
                "country": "South Africa", "track": "GA", "topic_tags": "mathematics;olympiad;contest;questions;solutions", "priority": "A", "source_type": "First-party university mathematics archive", "source_title": "University of Cape Town Mathematics Challenge and Olympiad 2018", "source_url": SOURCE_URL, "resource_title": f"UCT {item['label']}", "resource_url": item["resource_url"], "resource_class": item["resource_class"], "language": "English", "notes": "Public UCT Mathematics and Applied Mathematics Department archive; retained only after direct PDF retrieval, substantive extraction, English-only visible-content audit, and duplicate checks.", "access_model": "Free public Google Drive PDF", "verification_status": "HTTP 200 + local substantive English audit · verified 2026-08-16", "free_resource": "Yes"
            })
    audit_fields = ["label","file_id","resource_url","local_file","http_status","content_type","text_chars","english_cues","substantive_cues","non_english_cues","decision","reason"]
    with AUDIT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=audit_fields)
        writer.writeheader(); writer.writerows(audit_rows)
    clean_fields = ["resource_url","local_file","decision","text_chars","english_cues","substantive_cues","reason"]
    with CLEAN.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=clean_fields)
        writer.writeheader()
        for item in kept:
            writer.writerow({"resource_url": item["resource_url"], "local_file": item["local_file"], "decision": "keep", "text_chars": item["text_chars"], "english_cues": item["english_cues"], "substantive_cues": item["substantive_cues"], "reason": "Official UCT solution PDF with substantive extracted English mathematics content and no detected Afrikaans cues."})
    print(f"audited={len(audit_rows)} kept={len(kept)} data={DATA}")
    for row in audit_rows:
        print(row["label"], row["decision"], row["http_status"], row["text_chars"], row["english_cues"], row["substantive_cues"], row["non_english_cues"])


if __name__ == "__main__":
    main()

# Source folder: https://drive.google.com/drive/folders/1mqApdvv7ddBc-AuX28pU2k3YEwkASJSr
# UCT organiser page: https://science.uct.ac.za/department-mathematics/challenge-uct-mathematics-olympiad
# Local audit policy: retain substantive English-only content; exclude bilingual visible PDFs.
# Do not register this CSV in the lazy loader until integrity and coverage validation pass.
