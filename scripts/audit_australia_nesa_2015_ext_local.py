import csv
import subprocess
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
PDF_DIR = ROOT / 'research/australia_nesa_2015_ext_pdfs'
OUT = ROOT / 'research/australia_nesa_2015_ext_local_audit.csv'

FILES = [
    ('2015-ext1-exam', 'exam', 'Mathematics Extension 1', '2015-hsc-maths-ext1.pdf'),
    ('2015-ext1-guide', 'marking guidelines', 'Mathematics Extension 1', '2015-hsc-mg-maths-ext1.pdf'),
    ('2015-ext1-feedback', 'marking feedback', 'Mathematics Extension 1', '2015-hsc-maths-ext1-notes.pdf'),
    ('2015-ext2-exam', 'exam', 'Mathematics Extension 2', '2015-hsc-maths-ext2.pdf'),
    ('2015-ext2-guide', 'marking guidelines', 'Mathematics Extension 2', '2015-hsc-mg-maths-ext2.pdf'),
    ('2015-ext2-feedback', 'marking feedback', 'Mathematics Extension 2', '2015-hsc-maths-ext2-notes.pdf'),
]
BASE = 'https://www.nsw.gov.au/sites/default/files/noindex/2025-05/'
PAGES = {
    'Mathematics Extension 1': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-extension-1-archive/2015',
    'Mathematics Extension 2': 'https://www.nsw.gov.au/education-and-training/nesa/curriculum/hsc-exam-papers/mathematics-extension-2-archive/2015',
}


def extract_text(pdf: Path, text_path: Path):
    result = subprocess.run(
        ['pdftotext', '-layout', str(pdf), str(text_path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    text = text_path.read_text(errors='ignore') if text_path.exists() else ''
    return text, ' '.join(result.stderr.split())


def main():
    rows = []
    for key, kind, course, filename in FILES:
        pdf = PDF_DIR / filename
        text_path = PDF_DIR / f'{key}.txt'
        text, extractor_warning = extract_text(pdf, text_path) if pdf.exists() else ('', 'missing file')
        lower = text.lower()
        cues = sum(lower.count(term) for term in [
            'question', 'answer', 'mathematics', 'mark', 'calculate', 'show that', 'determine', 'solution'
        ])
        substantive = len(text.strip()) >= 800 and cues >= 3 and (
            'question' in lower or 'answer' in lower or 'mark' in lower or 'solution' in lower
        )
        rows.append({
            'key': key,
            'year': '2015',
            'course': course,
            'kind': kind,
            'page_url': PAGES[course],
            'resource_url': BASE + filename,
            'filename': filename,
            'status': 200 if pdf.exists() and pdf.stat().st_size > 0 else 0,
            'bytes': pdf.stat().st_size if pdf.exists() else 0,
            'text_chars': len(text),
            'english_cues': cues,
            'extractor_warning': extractor_warning,
            'substantive': 'keep' if substantive else 'review',
            'reason': (
                'Browser-downloaded official PDF; extracted text contains substantive English Mathematics Extension '
                'questions, marking criteria, or feedback.'
                if substantive else 'Missing or below substantive-content threshold.'
            ),
        })
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f'wrote {len(rows)} audit rows to {OUT}')
    print(f"keep={sum(row['substantive'] == 'keep' for row in rows)} review={sum(row['substantive'] != 'keep' for row in rows)}")
    for row in rows:
        print(row['key'], row['status'], row['bytes'], row['text_chars'], row['english_cues'], row['substantive'], row['extractor_warning'][:120])


if __name__ == '__main__':
    main()
