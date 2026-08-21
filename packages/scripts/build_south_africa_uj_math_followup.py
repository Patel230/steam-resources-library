from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data'
RESEARCH = ROOT / 'research'
OUTPUT = DATA / 'south_africa_uj_math_followup_verified_resources.csv'
AUDIT = RESEARCH / 'south_africa_uj_math_followup_local_audit.csv'
CLEAN = RESEARCH / 'clean_content_pdf_audit_south_africa_uj_math_followup.csv'
VERIFY_DATE = '2026-08-16'
FIELDS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
CANDIDATE_PAGES = [
    ('University of Johannesburg — Applied Mathematics 1A, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/APPLIED-MATHEMATICS-1A/9954607107691', 'https://ujcontent.uj.ac.za/view/pdfCoverPage?instCode=27UOJ_INST&filePid=1313518490007691&download=true'),
    ('University of Johannesburg — Mathematics 1B, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/MATHEMATICS-1B/9953798607691'),
    ('University of Johannesburg — Mathematics 1XB1, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/MATHEMATICS-1XB1/9953306107691'),
    ('University of Johannesburg — Mathematics 1C, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/MATHEMATICS-1C/9956005107691'),
    ('University of Johannesburg — Applied Mathematics, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/Applied-mathematics/9954710107691'),
    ('University of Johannesburg — Applied Mathematics 2A, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/APPLIED-MATHEMATICS-2A/9953504107691'),
    ('University of Johannesburg — Special Topics in Applied Mathematics, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/SPECIAL-TOPICS-IN-APPLIED-MATHEMATICS/9953504007691'),
    ('University of Johannesburg — Measurement Mathematics 1A, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/MEASUREMENT-MATHEMATICS-1A/9954805207691'),
    ('University of Johannesburg — APMA Applied Mathematics 1A, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/APMA-APPLIED-MATHEMATICS-1A/9953504407691'),
    ('University of Johannesburg — Engineering Mathematics 1A, 2024', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/ENGINEERING-MATHEMATICS-1A/9953702507691'),
]
ENGLISH = re.compile(r'\b(the|and|of|to|in|for|with|let|given|find|show|prove|question|problem|solution|exercise|answer|matrix|function|relation|graph|derivative|integral|equation|calculate|determine)\b', re.I)
QUESTIONS = re.compile(r'\b(question|problem|exercise|prove|show|find|calculate|determine|solve|let|given|derivative|integral|matrix|function|equation|evaluate|sketch)\b', re.I)

def existing_urls():
    urls = set()
    for path in DATA.glob('*_verified_resources.csv'):
        with path.open(newline='', encoding='utf-8') as fh:
            urls.update(r.get('resource_url','').strip() for r in csv.DictReader(fh) if r.get('resource_url'))
    return urls

def resolve_pdf(session: requests.Session, page_url: str):
    try:
        r = session.get(page_url, timeout=45, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        tag = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        pdf_url = unquote(tag.get('content','')) if tag else ''
        if '&amp;' in pdf_url:
            pdf_url = pdf_url.replace('&amp;', '&')
        title = (soup.find('meta', attrs={'name': 'citation_title'}) or {}).get('content', '')
        return r.status_code, pdf_url, title or page_url, r.headers.get('content-type','')
    except Exception as exc:
        return 0, '', page_url, f'error:{type(exc).__name__}'

def main():
    existing = existing_urls()
    audits, records, clean = [], [], []
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 Signal Atlas research audit'})
    with tempfile.TemporaryDirectory(prefix='uj-followup-') as td:
        for i, candidate in enumerate(CANDIDATE_PAGES):
            label, page_url = candidate[:2]
            known_pdf_url = candidate[2] if len(candidate) > 2 else ''
            page_status, resolved_pdf_url, meta_title, page_type = resolve_pdf(session, page_url)
            pdf_url = known_pdf_url or resolved_pdf_url
            pdf = Path(td) / f'{i}.pdf'
            textfile = Path(td) / f'{i}.txt'
            status, ctype = page_status, page_type
            text = ''
            if pdf_url:
                try:
                    response = session.get(pdf_url, timeout=60, verify=False)
                    status = response.status_code
                    ctype = response.headers.get('content-type','').lower()
                    pdf.write_bytes(response.content)
                except Exception as exc:
                    status = 0
                    ctype = f'error:{type(exc).__name__}'
            if pdf.exists() and pdf.read_bytes()[:4] == b'%PDF':
                parsed = subprocess.run(['pdftotext','-layout',str(pdf),str(textfile)], capture_output=True, text=True, timeout=45)
                if parsed.returncode == 0 and textfile.exists():
                    text = textfile.read_text(encoding='utf-8', errors='replace')
            chars = len(re.sub(r'\s+', '', text))
            english = len(ENGLISH.findall(text))
            questions = len(QUESTIONS.findall(text))
            duplicate = pdf_url in existing if pdf_url else False
            keep = bool(pdf_url) and status == 200 and pdf.exists() and pdf.read_bytes()[:4] == b'%PDF' and chars >= 500 and english >= 20 and questions >= 5 and not duplicate
            reason = 'keep' if keep else ('duplicate of existing catalog URL' if duplicate else ('no public PDF endpoint' if not pdf_url else 'not substantive English PDF'))
            audit = {'source_title': label, 'page_url': page_url, 'resource_url': pdf_url, 'page_status': str(page_status), 'http_status': str(status), 'content_type': ctype, 'text_chars': str(chars), 'english_cues': str(english), 'question_cues': str(questions), 'included': 'Yes' if keep else 'No', 'reason': reason}
            audits.append(audit)
            if keep:
                records.append({'country':'South Africa','track':'EM/DM','topic_tags':'mathematics;calculus;linear algebra;university exam questions','priority':'A','source_type':'First-party university repository','source_title':label,'source_url':page_url,'resource_title':label,'resource_url':pdf_url,'resource_class':'University past examination paper','language':'English','notes':'Open-access University of Johannesburg repository PDF; official record page resolves to a public PDF, local text extraction shows substantive mathematics questions, and duplicate checks passed.','access_model':'Free public PDF','verification_status':f'HTTP 200 · verified {VERIFY_DATE}','free_resource':'Yes'})
                clean.append({**audit, 'decision':'keep', 'evidence':f'text_chars={chars}; english_cues={english}; question_cues={questions}'})
    with AUDIT.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(audits[0].keys())); writer.writeheader(); writer.writerows(audits)
    with OUTPUT.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS); writer.writeheader(); writer.writerows(records)
    with CLEAN.open('w', newline='', encoding='utf-8') as fh:
        fields = list(clean[0].keys()) if clean else ['source_title','resource_url','decision','evidence']
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(clean)
    print({'candidates': len(CANDIDATE_PAGES), 'kept_new': len(records), 'audit': str(AUDIT.relative_to(ROOT)), 'clean': str(CLEAN.relative_to(ROOT))})
    for audit in audits:
        print(audit)

if __name__ == '__main__':
    main()
