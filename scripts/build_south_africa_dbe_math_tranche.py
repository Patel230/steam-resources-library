#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'research' / 'south_africa_dbe_math_local_audit.csv'
CLEAN = ROOT / 'research' / 'clean_content_pdf_audit_south_africa_dbe_math.csv'
OUT = ROOT / 'client' / 'src' / 'data' / 'south_africa_dbe_math_verified_resources.csv'
DOWNLOAD_DIR = ROOT / 'research' / 'downloads' / 'south_africa_dbe_math'

SESSION_URLS = {
    '2022 November NSC Mathematics': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2022NovemberExams.aspx',
    '2021 November NSC Mathematics': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2021NSCExamPapers.aspx',
    '2020 November NSC Mathematics': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2020NSCExamPapers.aspx',
    '2019 November NSC Mathematics': 'https://www.education.gov.za/2019NovExams.aspx',
}
HEADERS = {'User-Agent': 'Mozilla/5.0 SignalAtlas official-source audit'}
FIELDS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']


def existing_urls() -> set[str]:
    found = set()
    for path in (ROOT / 'client' / 'src' / 'data').glob('*.csv'):
        with path.open(encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f):
                found.add(row.get('resource_url', '').strip())
    return found


def download_and_text(url: str, dest: Path) -> tuple[int, str, str]:
    r = requests.get(url, headers=HEADERS, timeout=35, allow_redirects=True)
    dest.write_bytes(r.content)
    digest = hashlib.sha256(r.content).hexdigest()
    if r.status_code != 200 or not r.content.startswith(b'%PDF'):
        return r.status_code, digest, ''
    proc = subprocess.run(['pdftotext', '-layout', str(dest), '-'], capture_output=True, text=True, timeout=25)
    return r.status_code, digest, proc.stdout


def cues(text: str) -> tuple[int, int, int]:
    lower = text.lower()
    english = sum(lower.count(x) for x in (' the ', ' and ', ' question', 'answer', 'mathematics', 'paper'))
    substantive = sum(lower.count(x) for x in ('1.', '2.', '3.', 'marks', 'calculate', 'determine', 'prove', 'show that', 'solve'))
    non_english = sum(lower.count(x) for x in (' afrikaans', ' vraestel', ' tyd:', ' waar ', ' indien '))
    return english, substantive, non_english


def main() -> None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    seen = existing_urls()
    audit_rows: list[dict[str, str]] = []
    candidates: list[dict[str, str]] = []
    for session, page_url in SESSION_URLS.items():
        r = requests.get(page_url, headers=HEADERS, timeout=35)
        soup = BeautifulSoup(r.text, 'html.parser')
        heading = next((h for h in soup.find_all(['h2','h3']) if ' '.join(h.get_text(' ', strip=True).split()) == 'Mathematics'), None)
        if not heading:
            continue
        container = next((p for p in heading.parents if len(p.find_all('a', href=True)) >= 3), None)
        if not container:
            continue
        for a in container.find_all('a', href=True):
            label = ' '.join(a.get_text(' ', strip=True).split())
            if label not in ('Paper 1 (English)', 'Paper 2 (English)'):
                continue
            url = urljoin(r.url, a['href'])
            if url in seen or any(c['resource_url'] == url for c in candidates):
                audit_rows.append({'session': session, 'label': label, 'url': url, 'decision': 'duplicate', 'http_status': '', 'local_file': '', 'text_chars': '0', 'english_cues': '0', 'substantive_cues': '0', 'non_english_cues': '0', 'reason': 'URL already present or candidate duplicate'})
                continue
            filename = re.sub(r'[^a-z0-9]+', '_', f'{session}_{label}').strip('_').lower() + '.pdf'
            path = DOWNLOAD_DIR / filename
            status, digest, text = download_and_text(url, path)
            english, substantive, non_english = cues(text)
            decision = 'keep' if status == 200 and len(text) >= 1000 and english >= 8 and substantive >= 6 and non_english == 0 else 'exclude'
            reason = 'Substantive English-only Mathematics paper' if decision == 'keep' else f'Failed access/content policy: status={status}, chars={len(text)}, english={english}, substantive={substantive}, non_english={non_english}'
            row = {'session': session, 'label': label, 'url': url, 'decision': decision, 'http_status': str(status), 'local_file': filename, 'text_chars': str(len(text)), 'english_cues': str(english), 'substantive_cues': str(substantive), 'non_english_cues': str(non_english), 'reason': reason, 'sha256': digest}
            audit_rows.append(row)
            if decision == 'keep':
                candidates.append({'session': session, 'label': label, 'resource_url': url, 'local_file': filename, 'text_chars': str(len(text)), 'english_cues': str(english), 'substantive_cues': str(substantive)})
    with AUDIT.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['session','label','url','decision','http_status','local_file','text_chars','english_cues','substantive_cues','non_english_cues','reason','sha256'])
        writer.writeheader(); writer.writerows(audit_rows)
    rows = []
    clean = []
    for c in candidates:
        title = f"South African NSC Mathematics — {c['session'].replace(' Mathematics','')} {c['label']}"
        rows.append({
            'country': 'South Africa', 'track': 'GA', 'topic_tags': 'mathematics;secondary;exam;past paper', 'priority': 'A',
            'source_type': 'National examination authority', 'source_title': 'South African Department of Basic Education NSC Past Examination Papers',
            'source_url': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/NSCPastExaminationpapers.aspx',
            'resource_title': title, 'resource_url': c['resource_url'], 'resource_class': 'Question paper', 'language': 'English',
            'notes': 'Official public DBE Mathematics paper labelled English; retained only after local substantive-text audit and English-only visible-content check.',
            'access_model': 'Free public web resource', 'verification_status': 'Official source HTTP 200 + local substantive audit · verified 2026-08-16', 'free_resource': 'Yes'
        })
        clean.append({'resource_url': c['resource_url'], 'local_file': c['local_file'], 'decision': 'keep', 'text_chars': c['text_chars'], 'english_cues': c['english_cues'], 'substantive_cues': c['substantive_cues'], 'reason': 'Official DBE Mathematics paper labelled English; substantive English text and no detected Afrikaans cues.'})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    with CLEAN.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(clean[0]) if clean else ['resource_url','local_file','decision','text_chars','english_cues','substantive_cues','reason']); writer.writeheader(); writer.writerows(clean)
    print(f'candidates={len(audit_rows)} kept={len(rows)} out={OUT}')
    for row in rows: print(row['resource_title'], row['resource_url'])

if __name__ == '__main__':
    main()
