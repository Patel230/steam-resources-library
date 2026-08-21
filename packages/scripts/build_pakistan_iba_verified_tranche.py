#!/usr/bin/env python3
from __future__ import annotations

import csv, hashlib, re, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
INDEX = "https://admissions.iba.edu.pk/pastpapers.php"
AUDIT = ROOT / "research" / "pakistan_iba_entry_test_audit.csv"
OUT = ROOT / "client" / "src" / "data" / "pakistan_iba_verified_resources.csv"
CLEAN = ROOT / "research" / "clean_content_document_audit_pakistan_iba.csv"
FIELDS = ["country","track","topic_tags","priority","source_type","source_title","source_url","resource_title","resource_url","resource_class","language","notes","access_model","verification_status","free_resource"]
AUDIT_FIELDS = ["resource_url","http_status","content_type","bytes","sha256","pages","text_chars","math_cues","substantive_cues","decision","reason"]
BASE = {"country":"Pakistan","track":"GA","topic_tags":"aptitude;mathematics;entry test;MCQ;sample paper","priority":"A","source_type":"Official university admissions archive","source_title":"IBA Karachi Past Entry Test Papers","source_url":INDEX,"language":"English","access_model":"Free public web resource","verification_status":"Official source HTTP 200 + local substantive audit · verified 2026-08-16","free_resource":"Yes"}


def candidates():
    html = requests.get(INDEX, timeout=30, headers={"User-Agent":"Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")
    out = set()
    for a in soup.select("a[href]"):
        u = urljoin(INDEX, a["href"])
        label = (a.get_text(" ", strip=True) + " " + u).lower()
        if "iba.edu.pk" not in u and "emba.iba.edu.pk" not in u:
            continue
        if not (u.lower().endswith((".pdf", ".html", ".htm"))):
            continue
        if any(x in label for x in ("mathemat", "bba", "bs", "mba", "ms", "sample", "entry_test")):
            out.add(u)
    return sorted(out)


def audit(url):
    r0 = {k:"" for k in AUDIT_FIELDS}; r0["resource_url"] = url
    try:
        r = requests.get(url, timeout=35, headers={"User-Agent":"Mozilla/5.0"})
        r0["http_status"] = str(r.status_code); r0["content_type"] = r.headers.get("content-type", "").split(";")[0]; r0["bytes"] = str(len(r.content)); r0["sha256"] = hashlib.sha256(r.content).hexdigest()
        if r.status_code != 200:
            r0["decision"]="remove"; r0["reason"]="HTTP status not 200"; return r0
        if "pdf" in r0["content_type"].lower() or r.content.startswith(b"%PDF"):
            with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
                f.write(r.content); f.flush()
                text = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, timeout=30).stdout
                info = subprocess.run(["pdfinfo", f.name], capture_output=True, text=True, timeout=30).stdout
            m = re.search(r"^Pages:\s+(\d+)", info, re.M); r0["pages"] = m.group(1) if m else "0"
        else:
            text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
            r0["pages"] = "HTML"
        r0["text_chars"] = str(len(text))
        math = [r"\bmath", r"\balgebra", r"\bgeometry", r"\bprobability", r"\bfunction", r"\bequation", r"\bnumber", r"\bquantitative"]
        sub = [r"\bquestion", r"\bsolve", r"\bcalculate", r"\banswer", r"\bwhich of", r"\b(A|B|C|D)\b", r"\b1\.", r"\b2\.", r"\bmarks?\b"]
        mc = [p for p in math if re.search(p, text, re.I)]; sc = [p for p in sub if re.search(p, text, re.I)]
        r0["math_cues"] = ";".join(mc); r0["substantive_cues"] = ";".join(sc)
        if len(text) >= 300 and len(mc) >= 2 and len(sc) >= 2:
            r0["decision"]="keep"; r0["reason"]="public English document with mathematics and substantive question evidence"
        else:
            r0["decision"]="remove"; r0["reason"]="insufficient mathematics or substantive question evidence"
    except Exception as e:
        r0["decision"]="remove"; r0["reason"]=f"verification error: {type(e).__name__}"
    return r0


def title(url):
    return "IBA Karachi — " + Path(unquote(url).split("?")[0]).stem.replace("_", " ").replace("-", " ")


def main():
    urls = candidates(); existing = set()
    for p in (ROOT / "apps/web/src/data").glob("pakistan*.csv"):
        with p.open(encoding="utf-8", newline="") as f: existing.update(x.get("resource_url", "") for x in csv.DictReader(f))
    with ThreadPoolExecutor(max_workers=8) as ex:
        audits = list(ex.map(audit, urls))
    audits.sort(key=lambda x:x["resource_url"])
    with AUDIT.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f,fieldnames=AUDIT_FIELDS); w.writeheader(); w.writerows(audits)
    rows=[]; clean=[]
    for a in audits:
        if a["decision"] != "keep" or a["resource_url"] in existing: continue
        row=dict(BASE); row.update({"resource_title":title(a["resource_url"]),"resource_url":a["resource_url"],"resource_class":"Question paper","notes":"Official IBA Karachi public entry-test/sample-paper document retained after local substantive English mathematics-content audit; catalogued as GA practice."}); rows.append(row)
        clean.append({"resource_url":a["resource_url"],"local_file":Path(unquote(a["resource_url"]).split("?")[0]).name,"decision":"keep","text_chars":a["text_chars"],"english_cues":a["math_cues"],"substantive_cues":a["substantive_cues"],"reason":a["reason"]})
    with OUT.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    with CLEAN.open("w",encoding="utf-8",newline="") as f:
        fs=list(clean[0]) if clean else ["resource_url","local_file","decision","text_chars","english_cues","substantive_cues","reason"]
        w=csv.DictWriter(f,fieldnames=fs); w.writeheader(); w.writerows(clean)
    print(f"candidates={len(urls)} audited={len(audits)} keep={sum(a['decision']=='keep' for a in audits)} new_rows={len(rows)}")
    print(AUDIT); print(OUT); print(CLEAN)

if __name__ == "__main__": main()
