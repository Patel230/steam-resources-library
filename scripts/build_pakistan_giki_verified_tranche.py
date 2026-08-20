#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'research' / 'pakistan_giki_local_audit.csv'
CLEAN = ROOT / 'research' / 'clean_content_pdf_audit_pakistan_giki.csv'
OUT = ROOT / 'client' / 'src' / 'data' / 'pakistan_giki_verified_resources.csv'
DOWNLOAD_DIR = ROOT / 'research' / 'downloads' / 'pakistan_giki'
HEADERS = {'User-Agent': 'Mozilla/5.0 SignalAtlas official-source audit'}
CANDIDATES = [
    ('GIKI Engineering/Computing Sample Paper 2013', 'https://giki.edu.pk/wp-content/uploads/2019/10/SAMPAPER2013.pdf', 'Question paper'),
    ('GIKI Management Sciences Sample Tests', 'https://giki.edu.pk/wp-content/uploads/2019/10/Sample-Tests-for-BS-Management.pdf', 'Question paper'),
]
FIELDS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']

def existing_urls() -> set[str]:
    found = set()
    for path in (ROOT / 'client' / 'src' / 'data').glob('*.csv'):
        with path.open(encoding='utf-8', newline='') as f:
            found.update(row.get('resource_url', '').strip() for row in csv.DictReader(f))
    return found

def audit_pdf(url: str, path: Path):
    r = requests.get(url, headers=HEADERS, timeout=40, allow_redirects=True, verify=False)
    path.write_bytes(r.content)
    digest = hashlib.sha256(r.content).hexdigest()
    text = ''
    if r.status_code == 200 and r.content.startswith(b'%PDF'):
        p = subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True, timeout=30)
        text = p.stdout
    lower = text.lower()
    english = sum(lower.count(x) for x in (' the ', ' and ', ' question', 'answer', 'mathematics', 'mathematical', 'test'))
    substantive = sum(lower.count(x) for x in ('1.', '2.', '3.', 'marks', 'calculate', 'determine', 'solve', 'choose', 'select'))
    non_english = sum(lower.count(x) for x in (' afrikaans', ' urdu ', ' سوال', ' hindi '))
    return r.status_code, digest, text, english, substantive, non_english

def main():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    existing = existing_urls()
    audits, rows, clean = [], [], []
    for title, url, resource_class in CANDIDATES:
        filename = title.lower().replace('/', '-').replace(' ', '_') + '.pdf'
        path = DOWNLOAD_DIR / filename
        status, digest, text, english, substantive, non_english = audit_pdf(url, path)
        duplicate = url in existing
        decision = 'duplicate' if duplicate else ('keep' if status == 200 and len(text) >= 1000 and english >= 8 and substantive >= 6 and non_english == 0 else 'exclude')
        reason = 'Already present in live catalog' if duplicate else ('Official public substantive English sample paper' if decision == 'keep' else f'Failed policy: status={status}, chars={len(text)}, english={english}, substantive={substantive}, non_english={non_english}')
        audits.append({'title': title, 'url': url, 'decision': decision, 'http_status': status, 'local_file': filename, 'text_chars': len(text), 'english_cues': english, 'substantive_cues': substantive, 'non_english_cues': non_english, 'reason': reason, 'sha256': digest})
        if decision == 'keep':
            rows.append({'country':'Pakistan','track':'GA','topic_tags':'mathematics;aptitude;admission test;MCQ','priority':'A','source_type':'Official university admissions archive','source_title':'GIKI Undergraduate Admission Test Sample Papers','source_url':'https://giki.edu.pk/admissions/admissions-undergraduates/undergraduate-admission-test-syllabus/','resource_title':title,'resource_url':url,'resource_class':resource_class,'language':'English','notes':'Official public GIKI sample paper retained after local substantive English-content audit; covers mathematics or quantitative admission-test practice.','access_model':'Free public web resource','verification_status':'Official source HTTP 200 + local substantive audit · verified 2026-08-16','free_resource':'Yes'})
            clean.append({'resource_url':url,'local_file':filename,'decision':'keep','text_chars':len(text),'english_cues':english,'substantive_cues':substantive,'reason':reason})
    with AUDIT.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(audits[0])); writer.writeheader(); writer.writerows(audits)
    with OUT.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    with CLEAN.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(clean[0]) if clean else ['resource_url','local_file','decision','text_chars','english_cues','substantive_cues','reason']); writer.writeheader(); writer.writerows(clean)
    print(f'candidates={len(audits)} kept={len(rows)} out={OUT}')
    for row in rows: print(row['resource_title'], row['resource_url'])

if __name__ == '__main__':
    main()
