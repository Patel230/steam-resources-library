import csv
import subprocess
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DOWNLOADS = Path('/home/ubuntu/Downloads')
OUT = ROOT / 'research/australia_nesa_2016_2019_local_audit.csv'
BASE = 'https://www.nsw.gov.au'
FILES = {
    '2019-exam': ('2019', 'exam', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2019', '2019-hsc-mathematics.pdf', '/sites/default/files/noindex/2025-05/2019-hsc-mathematics.pdf'),
    '2019-guide': ('2019', 'guide', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2019', '2019-hsc-maths-mg.pdf', '/sites/default/files/noindex/2025-05/2019-hsc-maths-mg.pdf'),
    '2018-exam': ('2018', 'exam', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2018', '2018-hsc-mathematics.pdf', '/sites/default/files/noindex/2025-05/2018-hsc-mathematics.pdf'),
    '2018-guide': ('2018', 'guide', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2018', '2018-hsc-maths-mg.pdf', '/sites/default/files/noindex/2025-05/2018-hsc-maths-mg.pdf'),
    '2017-exam': ('2017', 'exam', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2017', '2017-hsc-maths.pdf', '/sites/default/files/noindex/2025-05/2017-hsc-maths.pdf'),
    '2017-guide': ('2017', 'guide', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2017', '2017-hsc-mg-mathematics.pdf', '/sites/default/files/noindex/2025-05/2017-hsc-mg-mathematics.pdf'),
    '2016-exam': ('2016', 'exam', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2016', '2016-hsc-maths.pdf', '/sites/default/files/noindex/2025-05/2016-hsc-maths.pdf'),
    '2016-guide': ('2016', 'guide', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2016', '2016-hsc-mg-maths.pdf', '/sites/default/files/noindex/2025-05/2016-hsc-mg-maths.pdf'),
}

rows = []
for key, (year, kind, page, filename, path) in FILES.items():
    pdf = DOWNLOADS / filename
    text_path = ROOT / 'research' / f'nesa_{key}.txt'
    status = 200 if pdf.exists() and pdf.stat().st_size > 0 else 0
    if status:
        subprocess.run(['pdftotext', '-layout', str(pdf), str(text_path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    text = text_path.read_text(errors='ignore') if text_path.exists() else ''
    lower = text.lower()
    cues = sum(lower.count(term) for term in ['question', 'answer', 'mathematics', 'mark', 'calculate', 'show that', 'determine'])
    substantive = len(text.strip()) >= 800 and cues >= 3 and ('question' in lower or 'answer' in lower or 'mark' in lower)
    rows.append({'key': key, 'year': year, 'kind': kind, 'page_url': page, 'resource_url': BASE + path, 'filename': filename, 'status': status, 'bytes': pdf.stat().st_size if pdf.exists() else 0, 'text_chars': len(text), 'english_cues': cues, 'substantive': 'keep' if substantive else 'review', 'reason': 'browser-downloaded official PDF with substantive English assessment evidence' if substantive else 'missing or below substantive-content threshold'})

with OUT.open('w', newline='', encoding='utf-8') as h:
    w = csv.DictWriter(h, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f'wrote {len(rows)} audit rows to {OUT}')
print(f'keep={sum(r["substantive"] == "keep" for r in rows)} review={sum(r["substantive"] != "keep" for r in rows)}')
for r in rows:
    print(r['key'], r['status'], r['bytes'], r['text_chars'], r['english_cues'], r['substantive'])
