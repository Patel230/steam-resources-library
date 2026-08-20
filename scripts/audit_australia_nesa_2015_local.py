import csv
import subprocess
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
PDF_DIR = ROOT / 'research/australia_nesa_2015_pdf'
OUT = ROOT / 'research/australia_nesa_2015_local_audit.csv'

FILES = [
    {
        'key': '2015-exam',
        'year': '2015',
        'kind': 'exam',
        'page_url': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2015',
        'resource_url': 'https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2015-maths-hsc-exam.pdf',
        'filename': '2015-maths-hsc-exam.pdf',
    },
    {
        'key': '2015-guide',
        'year': '2015',
        'kind': 'guide',
        'page_url': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-archive/2015',
        'resource_url': 'https://www.nsw.gov.au/sites/default/files/noindex/2025-05/2015-maths-hsc-mg.pdf',
        'filename': '2015-maths-hsc-mg.pdf',
    },
]


def extract_text(pdf: Path, text_path: Path) -> str:
    subprocess.run(
        ['pdftotext', '-layout', str(pdf), str(text_path)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return text_path.read_text(errors='ignore') if text_path.exists() else ''


def main() -> None:
    rows = []
    for item in FILES:
        pdf = PDF_DIR / item['filename']
        text_path = PDF_DIR / f"{item['key']}.txt"
        text = extract_text(pdf, text_path) if pdf.exists() else ''
        lower = text.lower()
        cues = sum(lower.count(term) for term in [
            'question', 'answer', 'mathematics', 'mark', 'calculate', 'show that', 'determine'
        ])
        substantive = len(text.strip()) >= 800 and cues >= 3 and (
            'question' in lower or 'answer' in lower or 'mark' in lower
        )
        rows.append({
            'key': item['key'],
            'year': item['year'],
            'kind': item['kind'],
            'page_url': item['page_url'],
            'resource_url': item['resource_url'],
            'filename': item['filename'],
            'status': 200 if pdf.exists() and pdf.stat().st_size > 0 else 0,
            'bytes': pdf.stat().st_size if pdf.exists() else 0,
            'text_chars': len(text),
            'english_cues': cues,
            'substantive': 'keep' if substantive else 'review',
            'reason': (
                'Browser-downloaded official PDF; pdftotext contains substantive English '
                'Mathematics examination or marking-guidelines evidence.'
                if substantive else
                'Missing or below substantive-content threshold.'
            ),
        })
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f'wrote {len(rows)} audit rows to {OUT}')
    print(f"keep={sum(row['substantive'] == 'keep' for row in rows)} review={sum(row['substantive'] != 'keep' for row in rows)}")
    for row in rows:
        print(row['key'], row['status'], row['bytes'], row['text_chars'], row['english_cues'], row['substantive'])


if __name__ == '__main__':
    main()
