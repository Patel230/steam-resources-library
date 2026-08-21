import csv
import subprocess
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
PDF_DIR = ROOT / 'research/australia_amt_pdfs'
OUT = ROOT / 'research/australia_amt_local_audit.csv'
BASE = 'https://amt.edu.au/wp-content/uploads/'

ITEMS = [
    ('amo-2019', '2019 AMO paper and solutions', 'Olympiad', '2020/05/AMO-2019-paper-and-solutions.pdf'),
    ('amo-2020', '2020 AMO paper and solutions', 'Olympiad', '2020/05/AMO-2020-paper-and-solutions.pdf'),
    ('amo-2016', '2016 AMO paper and solutions', 'Olympiad', '2019/02/2016-AMO-Paper-and-Solutions.pdf'),
    ('amo-2017', '2017 AMO paper and solutions', 'Olympiad', '2019/02/2017-AMO-Paper-and-Solutions.pdf'),
    ('amo-2018', '2018 AMO problems and solutions', 'Olympiad', '2019/02/AMO-2018-Problems-and-Solutions.pdf'),
    ('aimo-2017', '2017 AIMO paper and solutions', 'Olympiad', '2019/04/2017-AIMO-paper-solutions-v2019.pdf'),
    ('amc-senior', '2019 AMC practice problems and solutions — Senior', 'Practice questions', '2019/05/AMC-practice-problems-solutions-Set1-SEN.pdf'),
    ('amc-intermediate', '2019 AMC practice problems and solutions — Intermediate', 'Practice questions', '2019/05/AMC-practice-problems-solutions-Set1-INT.pdf'),
    ('amc-junior', '2019 AMC practice problems and solutions — Junior', 'Practice questions', '2019/05/AMC-practice-problems-solutions-Set1-JUN.pdf'),
    ('amc-upper-primary', '2019 AMC practice problems and solutions — Upper Primary', 'Practice questions', '2019/05/AMC-practice-problems-solutions-Set1-UPR.pdf'),
    ('amc-middle-primary', '2019 AMC practice problems and solutions — Middle Primary', 'Practice questions', '2019/05/AMC-practice-problems-solutions-Set1-MPR.pdf'),
]


def extract(pdf: Path, txt: Path):
    result = subprocess.run(['pdftotext', '-layout', str(pdf), str(txt)], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return (txt.read_text(errors='ignore') if txt.exists() else ''), ' '.join(result.stderr.split())


def main():
    rows = []
    for key, title, kind, relative in ITEMS:
        pdf = PDF_DIR / Path(relative).name
        txt = PDF_DIR / f'{key}.txt'
        text, warning = extract(pdf, txt) if pdf.exists() else ('', 'missing file')
        lower = text.lower()
        cues = sum(lower.count(term) for term in ['question', 'solution', 'answer', 'problem', 'calculate', 'prove', 'find', 'determine'])
        substantive = len(text.strip()) >= 800 and cues >= 4 and ('question' in lower or 'problem' in lower or 'solution' in lower)
        rows.append({
            'key': key, 'title': title, 'kind': kind,
            'page_url': 'https://amt.edu.au/department/past-papers',
            'resource_url': BASE + relative, 'filename': pdf.name,
            'status': 200 if pdf.exists() and pdf.stat().st_size else 0,
            'bytes': pdf.stat().st_size if pdf.exists() else 0,
            'text_chars': len(text), 'english_cues': cues,
            'extractor_warning': warning, 'substantive': 'keep' if substantive else 'review',
            'reason': 'Official AMT PDF contains substantive English mathematics problems and/or solutions.' if substantive else 'Missing or below substantive threshold.'
        })
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    print(f'wrote {len(rows)} rows to {OUT}')
    for row in rows:
        print(row['key'], row['status'], row['bytes'], row['text_chars'], row['english_cues'], row['substantive'], row['extractor_warning'][:120])

if __name__ == '__main__':
    main()
