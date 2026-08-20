import csv
import subprocess
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DOWNLOADS = Path('/home/ubuntu/Downloads')
OUT = ROOT / 'research/australia_nesa_2020_2023_local_audit.csv'
BASE = 'https://www.nsw.gov.au'
FILES = {
    '2020-exam': ('2020', 'exam', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-advanced/2020', 'nesa-2020-mathematics-advanced.pdf', '/sites/default/files/noindex/2025-05/2020-hsc-mathematics-advanced.pdf'),
    '2020-guide': ('2020', 'guide', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-advanced/2020', 'nesa-2020-guide.pdf', '/sites/default/files/noindex/2025-05/2020-hsc-mathematics-advanced-mg.pdf'),
    '2021-exam': ('2021', 'exam', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-advanced/2021', 'nesa-2021-exam.pdf', '/sites/default/files/noindex/2025-05/2021-hsc-mathematics-advanced.pdf'),
    '2021-guide': ('2021', 'guide', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-advanced/2021', 'nesa-2021-guide.pdf', '/sites/default/files/noindex/2025-05/2021-hsc-mathematics-advanced-mg.pdf'),
    '2022-exam': ('2022', 'exam', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-advanced/2022', 'nesa-2022-exam.pdf', '/sites/default/files/noindex/2025-05/2022-hsc-mathematics-advanced.pdf'),
    '2022-guide': ('2022', 'guide', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-advanced/2022', 'nesa-2022-guide.pdf', '/sites/default/files/noindex/2025-05/2022-hsc-mathematics-advanced-mg.pdf'),
    '2023-exam': ('2023', 'exam', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-advanced/2023', 'nesa-2023-exam.pdf', '/sites/default/files/noindex/2025-05/2023-hsc-maths-adv.pdf'),
    '2023-guide': ('2023', 'guide', 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-advanced/2023', 'nesa-2023-guide.pdf', '/sites/default/files/noindex/2025-05/2023-hsc-maths-adv-mg.pdf'),
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
    rows.append({'key': key, 'year': year, 'kind': kind, 'page_url': page, 'resource_url': BASE + path, 'filename': filename, 'status': status, 'bytes': pdf.stat().st_size if pdf.exists() else 0, 'text_chars': len(text), 'english_cues': cues, 'substantive': 'keep' if substantive else 'review', 'reason': 'browser-downloaded PDF with substantive English assessment evidence' if substantive else 'missing or below substantive-content threshold'})

with OUT.open('w', newline='', encoding='utf-8') as h:
    w = csv.DictWriter(h, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f'wrote {len(rows)} audit rows to {OUT}')
print(f'keep={sum(r["substantive"] == "keep" for r in rows)} review={sum(r["substantive"] != "keep" for r in rows)}')
for r in rows:
    print(r['key'], r['status'], r['bytes'], r['text_chars'], r['english_cues'], r['substantive'])
