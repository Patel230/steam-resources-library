#!/usr/bin/env python3
from __future__ import annotations

import csv, hashlib, re, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "client/src/data/pakistan_university_followup_verified_resources.csv"
AUDIT = ROOT / "research/pakistan_university_followup_audit.csv"
CLEAN = ROOT / "research/clean_content_pdf_audit_pakistan_university_followup.csv"
FIELDS = ["country","track","topic_tags","priority","source_type","source_title","source_url","resource_title","resource_url","resource_class","language","notes","access_model","verification_status","free_resource"]
AUDIT_FIELDS = ["resource_url","http_status","content_type","bytes","sha256","pages","text_chars","math_cues","substantive_cues","decision","reason"]
BASE = {"country":"Pakistan","track":"GA","topic_tags":"aptitude;mathematics;entry test;MCQ;sample questions","priority":"A","source_type":"Official university admissions archive","source_title":"","source_url":"","language":"English","access_model":"Free public web resource","verification_status":"Official source HTTP 200 + local substantive audit · verified 2026-08-16","free_resource":"Yes"}
SOURCE_META = {
    "neduet.edu.pk": ("NED University sample questions", "https://www.neduet.edu.pk/sites/default/files/Admissions-2025/sample_test_paper.pdf"),
    "nu.edu.pk": ("FAST NUCES admissions test guide", "https://www.nu.edu.pk/public/Downloads/TestGuide.pdf"),
    "umt.edu.pk": ("UMT entry-test sample page", "https://admissions.umt.edu.pk/Admission-Criteria/Entry-Test-Sample.aspx"),
}
URLS = [
    "https://www.neduet.edu.pk/sites/default/files/Admissions-2025/sample_test_paper.pdf",
    "https://www.nu.edu.pk/public/Downloads/TestGuide.pdf",
    "https://admissions.umt.edu.pk/Admission-Criteria/Entry-Test-Sample.aspx",
    "https://admissions.pieas.edu.pk/Admissions/Contents/Information%20leaflet%20BS-Programs-2025.pdf",
]


def audit(url: str):
    out = {k: "" for k in AUDIT_FIELDS}; out["resource_url"] = url
    try:
        r = requests.get(url, timeout=35, headers={"User-Agent": "Mozilla/5.0"})
        out["http_status"] = str(r.status_code); out["content_type"] = r.headers.get("content-type", "").split(";")[0]; out["bytes"] = str(len(r.content)); out["sha256"] = hashlib.sha256(r.content).hexdigest()
        if r.status_code != 200:
            out["decision"] = "remove"; out["reason"] = "HTTP status not 200"; return out
        if "pdf" in out["content_type"].lower() or r.content.startswith(b"%PDF"):
            with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
                f.write(r.content); f.flush()
                text = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, timeout=30).stdout
                info = subprocess.run(["pdfinfo", f.name], capture_output=True, text=True, timeout=30).stdout
            m = re.search(r"^Pages:\s+(\d+)", info, re.M); out["pages"] = m.group(1) if m else "0"
        else:
            text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True); out["pages"] = "HTML"
        out["text_chars"] = str(len(text))
        math_patterns = [r"\bmath", r"\balgebra", r"\bgeometry", r"\bprobability", r"\bfunction", r"\bequation", r"\bnumber", r"\bquantitative", r"\bcalculus", r"\btrigonometry"]
        substantive_patterns = [r"\bquestion", r"\bsolve", r"\bcalculate", r"\banswer", r"which of", r"\b(A|B|C|D)\b", r"\b1\.", r"\b2\.", r"\bmarks?\b", r"sample questions"]
        mc = [p for p in math_patterns if re.search(p, text, re.I)]; sc = [p for p in substantive_patterns if re.search(p, text, re.I)]
        out["math_cues"] = ";".join(mc); out["substantive_cues"] = ";".join(sc)
        if len(text) >= 300 and len(mc) >= 2 and len(sc) >= 2:
            out["decision"] = "keep"; out["reason"] = "public English document with mathematics and substantive question evidence"
        else:
            out["decision"] = "remove"; out["reason"] = "insufficient mathematics or substantive question evidence"
    except Exception as exc:
        out["decision"] = "remove"; out["reason"] = f"verification error: {type(exc).__name__}"
    return out


def title(url: str) -> str:
    host = "NEDUET" if "neduet" in url else "FAST NUCES" if "nu.edu.pk" in url else "UMT" if "umt.edu.pk" in url else "PIEAS"
    stem = Path(unquote(url).split("?")[0]).stem.replace("_", " ").replace("-", " ")
    return f"{host} — {stem}"


def main():
    existing = set()
    for p in (ROOT / "client/src/data").glob("pakistan*.csv"):
        with p.open(encoding="utf-8", newline="") as f:
            existing.update(row.get("resource_url", "").strip().lower() for row in csv.DictReader(f))
    with ThreadPoolExecutor(max_workers=4) as pool:
        audits = list(pool.map(audit, URLS))
    audits.sort(key=lambda row: row["resource_url"])
    with AUDIT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDS); writer.writeheader(); writer.writerows(audits)
    rows, clean = [], []
    for a in audits:
        if a["decision"] != "keep" or a["resource_url"].lower() in existing:
            continue
        row = dict(BASE)
        meta = next((value for host, value in SOURCE_META.items() if host in a["resource_url"]), ("Pakistan university public entry-test sample material", a["resource_url"]))
        row.update({"source_title": meta[0], "source_url": meta[1], "resource_title": title(a["resource_url"]), "resource_url": a["resource_url"], "resource_class": "Question paper", "notes": "Official Pakistani university public sample or test-guide material retained after local substantive English mathematics/aptitude audit; catalogued as GA practice."})
        rows.append(row)
        clean.append({"resource_url": a["resource_url"], "local_file": Path(unquote(a["resource_url"]).split("?")[0]).name, "decision": "keep", "text_chars": a["text_chars"], "english_cues": a["math_cues"], "substantive_cues": a["substantive_cues"], "reason": a["reason"]})
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    with CLEAN.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["resource_url","local_file","decision","text_chars","english_cues","substantive_cues","reason"]); writer.writeheader(); writer.writerows(clean)
    print(f"candidates={len(URLS)} audited={len(audits)} keep={sum(a['decision']=='keep' for a in audits)} new_rows={len(rows)}")
    print(AUDIT); print(OUT); print(CLEAN)


if __name__ == "__main__":
    main()
