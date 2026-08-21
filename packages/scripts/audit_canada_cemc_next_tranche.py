from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "canada_cemc_next_tranche_audit.csv"
CATALOG = ROOT / "client" / "src" / "data"
URLS = [
    "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025BCCContest5_6.pdf",
    "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025BCCContestSolutions5_6.pdf",
    "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025BCCContest7_8.pdf",
    "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025BCCContestSolutions7_8.pdf",
    "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025BCCContest9_10.pdf",
]

existing = set()
for path in CATALOG.glob("*_verified_resources.csv"):
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            existing.add(row.get("resource_url", "").strip())

rows = []
OUT.parent.mkdir(parents=True, exist_ok=True)
fieldnames = ["url", "status", "content_type", "bytes", "pdf", "pages", "english_markers", "question_markers", "duplicate", "error"]
with OUT.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()

for url in URLS:
    record = {"url": url, "status": "", "content_type": "", "bytes": 0, "pdf": False, "pages": 0, "english_markers": 0, "question_markers": 0, "duplicate": url in existing, "error": ""}
    try:
        request = Request(url, headers={"User-Agent": "SignalAtlasResearch/1.0"})
        with urlopen(request, timeout=4) as response:
            body = response.read()
            record["status"] = response.status
            record["content_type"] = response.headers.get_content_type()
            record["bytes"] = len(body)
        record["pdf"] = body.startswith(b"%PDF")
        if record["pdf"]:
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(body)).pages)
            record["pages"] = len(PdfReader(io.BytesIO(body)).pages)
            record["english_markers"] = len(re.findall(r"\b(the|and|question|answer|contest|solution|mathematics)\b", text, re.I))
            record["question_markers"] = len(re.findall(r"\b(question|problem|calculate|determine|which|how many)\b", text, re.I))
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    rows.append(record)
    with OUT.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writerow(record)
        handle.flush()
    print(record, flush=True)
print(f"Wrote {OUT}")
for row in rows:
    print(row)
