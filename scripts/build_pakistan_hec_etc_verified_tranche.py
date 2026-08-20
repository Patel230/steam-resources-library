from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "client" / "src" / "data"
RESEARCH_DIR = ROOT / "research"
OUT_CSV = DATA_DIR / "pakistan_hec_etc_verified_resources.csv"
AUDIT_CSV = RESEARCH_DIR / "pakistan_hec_etc_local_audit.csv"
CLEAN_CSV = RESEARCH_DIR / "clean_content_pdf_audit_pakistan_hec_etc.csv"

FIELDS = ["country","track","topic_tags","priority","source_type","source_title","source_url","resource_title","resource_url","resource_class","language","notes","access_model","verification_status","free_resource"]

CANDIDATES = [
    ("HAT Engineering MS", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-HAT-ENGINEERING-%28MS%29.pdf", "Engineering Mathematics; quantitative reasoning", "Engineering and quantitative sample paper"),
    ("HAT General MS", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-HAT-GENERAL%20%28MS%29.pdf", "General aptitude; quantitative reasoning", "General aptitude sample paper"),
    ("HAT Management Sciences MS", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-HAT-MANAGEMENT%20SCIENCES-%28MS%29.pdf", "General aptitude; quantitative reasoning", "Management aptitude sample paper"),
    ("HAT Arts and Humanities MS", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-HAT-ARTS%20AND%20HUMANITIES%20%28MS%29.pdf", "General aptitude; analytical reasoning", "Arts and humanities aptitude sample paper"),
    ("HAT Medical MS", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-HAT-MEDICAL%28MS%29.pdf", "General aptitude; quantitative reasoning", "Medical aptitude sample paper"),
    ("USAT Arts and Humanities", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-USAT-ARTS%20%26%20HUMANITIES.pdf", "General aptitude; verbal and quantitative reasoning", "Undergraduate studies aptitude sample paper"),
    ("USAT Commerce", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-USAT-COMMERCE.pdf", "General aptitude; quantitative reasoning", "Undergraduate commerce aptitude sample paper"),
    ("USAT Computer Science", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-USAT-COMPUTER%20SCIENCE.pdf", "General aptitude; quantitative reasoning", "Undergraduate computer-science aptitude sample paper"),
    ("USAT General Science", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-USAT-GENERAL%20SCIENCE.pdf", "General aptitude; quantitative reasoning", "Undergraduate general-science aptitude sample paper"),
    ("USAT Pre-Engineering", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-USAT-PRE-ENGINEERING.pdf", "General aptitude; engineering mathematics", "Undergraduate pre-engineering aptitude sample paper"),
    ("USAT Pre-Medical", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-USAT-PRE-MEDICAL.pdf", "General aptitude; quantitative reasoning", "Undergraduate pre-medical aptitude sample paper"),
    ("Law-GAT", "https://www.hec.gov.pk/english/services/students/etc/PublishingImages/LAW%20GAT%20Sample%20Paper.pdf", "General aptitude; analytical reasoning", "Law-GAT sample paper"),
    ("BFAP USAT Arts and Humanities", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-BFAP-USAT-ARTS%20%26%20HUMANITIES.pdf", "General aptitude; verbal and quantitative reasoning", "Balochistan and FATA scholarship aptitude sample paper"),
    ("BFAP USAT Commerce", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-BFAP-USAT-COMMERCE.pdf", "General aptitude; quantitative reasoning", "Balochistan and FATA commerce aptitude sample paper"),
    ("BFAP USAT Computer Science", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-BFAP-USAT-COMPUTER%20SCIENCE.pdf", "General aptitude; quantitative reasoning", "Balochistan and FATA computer-science aptitude sample paper"),
    ("BFAP USAT General Science", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-BFAP-USAT-GENERAL%20SCIENCE.pdf", "General aptitude; quantitative reasoning", "Balochistan and FATA general-science aptitude sample paper"),
    ("BFAP USAT Pre-Engineering", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-BFAP-USAT-PRE-ENGINEERING.pdf", "General aptitude; engineering mathematics", "Balochistan and FATA pre-engineering aptitude sample paper"),
    ("BFAP USAT Pre-Medical", "https://www.hec.gov.pk/english/services/students/etc/Documents/SAMPLE%20PAPER-BFAP-USAT-PRE-MEDICAL.pdf", "General aptitude; quantitative reasoning", "Balochistan and FATA pre-medical aptitude sample paper"),
]

QUESTION_RE = re.compile(r"\b(question|questions|choose|select|answer|calculate|solve|which|what|following|problem|mcq|multiple choice)\b", re.I)
ENGLISH_RE = re.compile(r"\b(the|and|of|to|in|for|with|this|that|is|are|you|your|from|by|on|as|an|a)\b", re.I)

def text_from_pdf(content: bytes) -> str:
    with tempfile.TemporaryDirectory(prefix="hec-etc-") as td:
        path = Path(td) / "resource.pdf"
        path.write_bytes(content)
        proc = subprocess.run(["pdftotext", "-f", "1", "-l", "12", str(path), "-"], capture_output=True, text=True, timeout=45)
        return proc.stdout[:100000]

def existing_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA_DIR.glob("*.csv"):
        try:
            with path.open(newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    urls.add(row.get("resource_url", "").strip())
        except Exception:
            continue
    return urls

def audit(item):
    title, url, tags, resource_title = item
    result = {"title": title, "url": url, "http_status":"", "content_type":"", "bytes":"", "english_hits":"", "question_hits":"", "decision":"remove", "evidence":""}
    try:
        try:
            response = requests.get(url, timeout=35, allow_redirects=True, headers={"User-Agent":"SignalAtlasCleanContentAudit/1.0"}, verify=False)
            content = response.content
            status = response.status_code
            content_type = response.headers.get("content-type", "")
        except requests.RequestException:
            with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
                proc = subprocess.run(["curl", "-k", "-L", "--max-time", "45", "--retry", "2", "-A", "SignalAtlasCleanContentAudit/1.0", "-o", tmp.name, "-w", "%{http_code}", url], capture_output=True, text=True, timeout=60)
                content = Path(tmp.name).read_bytes()
                status = int(proc.stdout.strip() or "0")
                content_type = "application/pdf" if content.startswith(b"%PDF") else ""
        result.update(http_status=str(status), content_type=content_type, bytes=str(len(content)))
        if status != 200 or not ("pdf" in content_type.lower() or content.startswith(b"%PDF")):
            result["evidence"] = "not a direct HTTP 200 PDF"
            return result
        text = text_from_pdf(content)
        english_hits = len(ENGLISH_RE.findall(text))
        question_hits = len(QUESTION_RE.findall(text))
        result.update(english_hits=str(english_hits), question_hits=str(question_hits))
        result["evidence"] = f"extracted_chars={len(text)}; english_hits={english_hits}; question_hits={question_hits}"
        if english_hits >= 10 and question_hits >= 8 and len(text) >= 500:
            result["decision"] = "keep"
    except Exception as exc:
        result["evidence"] = f"{type(exc).__name__}: {exc}"
    return result

def main():
    existing = existing_urls()
    with ThreadPoolExecutor(max_workers=8) as executor:
        audits = list(executor.map(audit, CANDIDATES))
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    with AUDIT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(audits[0].keys()))
        writer.writeheader(); writer.writerows(audits)
    kept = []
    clean_rows = []
    for item, result in zip(CANDIDATES, audits):
        title, url, tags, resource_title = item
        if result["decision"] != "keep" or url in existing:
            continue
        track = "EM" if "engineering" in tags.lower() else "GA"
        kept.append({"country":"Pakistan","track":track,"topic_tags":tags,"priority":"Top-100 country expansion","source_type":"Official national assessment body","source_title":"HEC Education Testing Council Sample Papers","source_url":"https://www.hec.gov.pk/english/services/students/etc/Pages/HAT-Sample-Papers.aspx","resource_title":resource_title,"resource_url":url,"resource_class":"exam / practice / MCQ","language":"English","notes":"Official HEC ETC public sample paper; substantive question material verified locally.","access_model":"free public PDF","verification_status":"verified","free_resource":"yes"})
        clean_rows.append({**result,"decision":"keep"})
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS); writer.writeheader(); writer.writerows(kept)
    with CLEAN_CSV.open("w", newline="", encoding="utf-8") as fh:
        fields = list(clean_rows[0].keys()) if clean_rows else list(audits[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(clean_rows)
    print({"candidates":len(CANDIDATES),"audited":len(audits),"kept_new":len(kept),"audit_decisions":{k:sum(1 for r in audits if r["decision"]==k) for k in ["keep","remove"]},"out_csv":str(OUT_CSV.relative_to(ROOT)),"audit_csv":str(AUDIT_CSV.relative_to(ROOT)),"clean_csv":str(CLEAN_CSV.relative_to(ROOT))})
    for row in kept:
        print(row["resource_title"], row["resource_url"])

if __name__ == "__main__":
    main()
