import csv
import subprocess
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
PDF_DIR = ROOT / 'research/australia_nesa_2014_mg_pdfs'
OUT = ROOT / 'research/australia_nesa_2014_mg_local_audit.csv'
PAGE_URL = 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-general-archive/2014'
BASE = 'https://www.nsw.gov.au/sites/default/files/noindex/2025-05/'

FILES = [
    ('2014-exam', 'exam', '2014-maths-general-hsc-exam.pdf'),
    ('2014-specimen', 'specimen exam', '2014-maths-general-2-specimen-paper.pdf'),
    ('2014-worked-solutions', 'worked solutions', '2014-maths-general-2-worked-solutions.pdf'),
    ('2014-guide', 'marking guidelines', '2014-maths-general-hsc-mg.pdf'),
    ('2014-feedback', 'marking feedback', 'maths-general-hsc-notes-2014.pdf'),
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
    for key, kind, filename in FILES:
        pdf = PDF_DIR / filename
        text_path = PDF_DIR / f'{key}.txt'
        text = extract_text(pdf, text_path) if pdf.exists() else ''
        lower = text.lower()
        cues = sum(lower.count(term) for term in [
            'question', 'answer', 'mathematics', 'mark', 'calculate', 'show that', 'determine', 'solution'
        ])
        substantive = len(text.strip()) >= 800 and cues >= 3 and (
            'question' in lower or 'answer' in lower or 'mark' in lower or 'solution' in lower
        )
        rows.append({
            'key': key,
            'year': '2014',
            'kind': kind,
            'page_url': PAGE_URL,
            'resource_url': BASE + filename,
            'filename': filename,
            'status': 200 if pdf.exists() and pdf.stat().st_size > 0 else 0,
            'bytes': pdf.stat().st_size if pdf.exists() else 0,
            'text_chars': len(text),
            'english_cues': cues,
            'substantive': 'keep' if substantive else 'review',
            'reason': (
                'Browser-downloaded official PDF; pdftotext contains substantive English '
                'Mathematics General questions, worked solutions, marking criteria, or feedback.'
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
