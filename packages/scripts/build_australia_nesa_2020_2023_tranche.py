import csv
import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data'
OUT = DATA / 'australia_nesa_2020_2023_verified_resources.csv'
AUDIT = ROOT / 'research/australia_nesa_2020_2023_content_audit.csv'
DOWNLOADS = ROOT / 'research/australia_nesa_2020_2023_pdfs'
COLUMNS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
BASE = 'https://www.nsw.gov.au'
ITEMS = []
for year in range(2020, 2024):
    page = f'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-advanced/{year}'
    if year == 2023:
        exam = '/sites/default/files/noindex/2025-05/2023-hsc-maths-adv.pdf'
        guide = '/sites/default/files/noindex/2025-05/2023-hsc-maths-adv-mg.pdf'
    elif year == 2022:
        exam = '/sites/default/files/noindex/2025-05/2022-hsc-mathematics-advanced.pdf'
        guide = '/sites/default/files/noindex/2025-05/2022-hsc-mathematics-advanced-mg.pdf'
    elif year == 2021:
        exam = '/sites/default/files/noindex/2025-05/2021-hsc-mathematics-advanced.pdf'
        guide = '/sites/default/files/noindex/2025-05/2021-hsc-mathematics-advanced-mg.pdf'
    else:
        exam = '/sites/default/files/noindex/2025-05/2020-hsc-mathematics-advanced.pdf'
        guide = '/sites/default/files/noindex/2025-05/2020-hsc-mathematics-advanced-mg.pdf'
    ITEMS.extend([(year, 'exam', page, urljoin(BASE, exam)), (year, 'guide', page, urljoin(BASE, guide))])


def existing_urls():
    urls = set()
    for path in DATA.glob('*.csv'):
        if path in {OUT, DATA / 'final_resources.csv'}:
            continue
        with path.open(newline='', encoding='utf-8') as h:
            urls.update(r.get('resource_url', '').strip().lower() for r in csv.DictReader(h) if r.get('resource_url'))
    return urls


def audit_pdf(year, kind, url):
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    name = f'{year}_mathematics_advanced_{kind}.pdf'
    pdf = DOWNLOADS / name
    response = requests.get(url, timeout=40, headers={'User-Agent': 'Signal-Atlas verification bot/1.0'})
    content_type = response.headers.get('content-type', '').lower()
    status = response.status_code
    pdf.write_bytes(response.content)
    text_file = pdf.with_suffix('.txt')
    subprocess.run(['pdftotext', '-layout', str(pdf), str(text_file)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    text = text_file.read_text(errors='ignore') if text_file.exists() else ''
    lower = text.lower()
    english_cues = sum(lower.count(term) for term in ['question', 'answer', 'mathematics', 'mark', 'calculate', 'show that', 'determine'])
    substantive = len(text.strip()) >= 800 and english_cues >= 3 and ('question' in lower or 'answer' in lower or 'mark' in lower)
    keep = status == 200 and 'pdf' in content_type and substantive
    return {'year': year, 'kind': kind, 'url': url, 'status': status, 'content_type': content_type, 'bytes': len(response.content), 'text_chars': len(text), 'english_cues': english_cues, 'substantive': 'keep' if keep else 'review', 'reason': 'direct public PDF with substantive English assessment evidence' if keep else 'failed direct PDF or substantive-content threshold'}


def main():
    dup = existing_urls()
    audits = []
    rows = []
    for year, kind, page, url in ITEMS:
        result = audit_pdf(year, kind, url)
        audits.append(result)
        if result['substantive'] != 'keep':
            print(f"REVIEW {year} {kind}: {result['status']} {result['content_type']} chars={result['text_chars']}")
            continue
        if url.lower() in dup:
            print(f'DUPLICATE {url}')
            continue
        title_kind = 'marking guidelines' if kind == 'guide' else 'examination paper'
        rows.append({'country':'Australia','track':'EM','topic_tags':'mathematics;calculus;functions;probability;statistics;algebra;geometry;assessment;past year questions','priority':'A','source_type':'State examination authority archive','source_title':'NSW Education Standards Authority Mathematics Advanced HSC exam archive (official)','source_url':page,'resource_title':f'NSW NESA {year} Mathematics Advanced — {title_kind}','resource_url':url,'resource_class':'Solution archive' if kind == 'guide' else 'Exam paper','language':'English','notes':'Official NSW NESA public English Mathematics Advanced HSC assessment document; substantive examination or marking-guideline PDF retained.','access_model':'Free public web resource','verification_status':'HTTP 200 + application/pdf + local substantive audit · verified 2026-08-16','free_resource':'Yes'})
    with AUDIT.open('w', newline='', encoding='utf-8') as h:
        aw = csv.DictWriter(h, fieldnames=list(audits[0].keys()))
        aw.writeheader(); aw.writerows(audits)
    with OUT.open('w', newline='', encoding='utf-8') as h:
        w = csv.DictWriter(h, fieldnames=COLUMNS)
        w.writeheader(); w.writerows(rows)
    print(f'wrote {len(rows)} rows to {OUT}')
    print(f'audit {len(audits)} candidates: {sum(a["substantive"] == "keep" for a in audits)} keep, {sum(a["substantive"] != "keep" for a in audits)} review')


if __name__ == '__main__':
    main()
