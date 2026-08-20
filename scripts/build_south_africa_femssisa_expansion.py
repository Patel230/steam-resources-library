#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PAGE = "https://saolympiads.co.za/past-papers/"
AUDIT = ROOT / "research" / "south_africa_femssisa_expansion_audit.csv"
OUT = ROOT / "client" / "src" / "data" / "south_africa_femssisa_expansion_verified_resources.csv"
CLEAN = ROOT / "research" / "clean_content_pdf_audit_south_africa_femssisa_expansion.csv"

FIELDS = ["country","track","topic_tags","priority","source_type","source_title","source_url","resource_title","resource_url","resource_class","language","notes","access_model","verification_status","free_resource"]
AUDIT_FIELDS = ["filename","resource_url","http_status","content_type","bytes","sha256","pages","text_chars","english_cues","substantive_cues","decision","reason"]

BASE = {
    "country": "South Africa",
    "track": "GA",
    "topic_tags": "mathematics;olympiad;problem solving;multiple choice",
    "priority": "B",
    "source_type": "Official olympiad organizer",
    "source_title": "SA Olympiads Past Papers (official)",
    "source_url": PAGE,
    "language": "English",
    "access_model": "Free public web resource",
    "verification_status": "Official source HTTP 200 + local substantive audit · verified 2026-08-16",
    "free_resource": "Yes",
}


def fetch_candidates() -> list[str]:
    html = requests.get(PAGE, timeout=30, headers={"User-Agent": "Mozilla/5.0"}).text
    urls = sorted(set(re.findall(r"https://saolympiads\.co\.za/wp-content/uploads/[^\"' ]+\.pdf", html)))
    # Pure Mathematics Olympiad files only. Exclude Afrikaans variants and mathematical-literacy files.
    return [u for u in urls if "FEMSSISA" in unquote(u) and "Afrikaans" not in unquote(u) and "ENGLISH" not in unquote(u).upper() and "MATH" in unquote(u).upper()]


def title_for(url: str) -> str:
    name = Path(unquote(url).split("?")[0]).stem.replace("_", " ").replace("-", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return f"SA Olympiads — {name}"


def audit(url: str) -> dict[str, str]:
    filename = Path(unquote(url).split("?")[0]).name
    result = {k: "" for k in AUDIT_FIELDS}
    result["filename"] = filename
    result["resource_url"] = url
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        result["http_status"] = str(r.status_code)
        result["content_type"] = r.headers.get("content-type", "").split(";")[0]
        result["bytes"] = str(len(r.content))
        result["sha256"] = hashlib.sha256(r.content).hexdigest()
        if r.status_code != 200 or "pdf" not in result["content_type"].lower() or not r.content.startswith(b"%PDF"):
            result["decision"] = "remove"
            result["reason"] = "not a directly accessible PDF"
            return result
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(r.content); f.flush()
            txt = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, timeout=30).stdout
            info = subprocess.run(["pdfinfo", f.name], capture_output=True, text=True, timeout=30).stdout
        pages = re.search(r"^Pages:\s+(\d+)", info, re.M)
        result["pages"] = pages.group(1) if pages else "0"
        result["text_chars"] = str(len(txt))
        english = [r"\bmathematics?\b", r"\bquestion", r"\banswer", r"\bgrade\b", r"\btotal\b", r"\bchoose\b", r"\bcalculate\b", r"\bsolve\b"]
        substantive = [r"\bquestion", r"\bsolve", r"\bcalculate", r"\bwhich of the following", r"\banswer", r"\btotal", r"\b1\.", r"\b2\.", r"\(a\)"]
        ec = [p for p in english if re.search(p, txt, re.I)]
        sc = [p for p in substantive if re.search(p, txt, re.I)]
        result["english_cues"] = ";".join(ec)
        result["substantive_cues"] = ";".join(sc)
        if len(txt.strip()) >= 250 and len(ec) >= 2 and len(sc) >= 2:
            result["decision"] = "keep"
            result["reason"] = "HTTP 200 PDF with visible English and substantive mathematics question/answer evidence"
        else:
            result["decision"] = "remove"
            result["reason"] = "insufficient visible English or substantive-content evidence"
    except Exception as exc:
        result["decision"] = "remove"
        result["reason"] = f"verification error: {type(exc).__name__}"
    return result


def main() -> None:
    candidates = fetch_candidates()
    existing = set()
    for p in (ROOT / "client" / "src" / "data").glob("south_africa*.csv"):
        with p.open(encoding="utf-8", newline="") as f:
            existing.update(row.get("resource_url", "") for row in csv.DictReader(f))
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(audit, u) for u in candidates]
        audited = [f.result() for f in as_completed(futures)]
    audited.sort(key=lambda r: r["resource_url"])
    with AUDIT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=AUDIT_FIELDS); w.writeheader(); w.writerows(audited)
    rows, clean = [], []
    for a in audited:
        if a["decision"] != "keep" or a["resource_url"] in existing:
            continue
        row = dict(BASE)
        row.update({
            "resource_title": title_for(a["resource_url"]),
            "resource_url": a["resource_url"],
            "resource_class": "Question paper" if "ANSWER" not in a["filename"].upper() else "Answer key",
            "notes": "Official public South African FEMSSISA Mathematics Olympiad PDF retained after local substantive English-content audit; direct document contains visible mathematics questions or answer material and is catalogued as GA practice.",
        })
        rows.append(row)
        clean.append({"resource_url": a["resource_url"], "local_file": a["filename"], "decision": "keep", "text_chars": a["text_chars"], "english_cues": a["english_cues"], "substantive_cues": a["substantive_cues"], "reason": a["reason"]})
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    with CLEAN.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(clean[0]) if clean else ["resource_url","local_file","decision","text_chars","english_cues","substantive_cues","reason"]); w.writeheader(); w.writerows(clean)
    print(f"candidates={len(candidates)} audited={len(audited)} keep={sum(a['decision']=='keep' for a in audited)} new_rows={len(rows)}")
    print(f"wrote {AUDIT}")
    print(f"wrote {OUT}")
    print(f"wrote {CLEAN}")


if __name__ == "__main__":
    main()

