from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'client/src/data'
URL_AUDIT = ROOT / 'research/australia_scsa_url_audit.csv'
CONTENT_AUDIT = ROOT / 'research/australia_scsa_2022_2025_content_audit.csv'
OUTPUT = DATA / 'australia_scsa_2020_2021_verified_resources.csv'
COLUMNS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
PAGES = {
    'MAM': 'https://senior-secondary.scsa.wa.edu.au/further-resources/past-atar-course-exams/mathematics-methods-past-atar-course-exams',
    'MAS': 'https://senior-secondary.scsa.wa.edu.au/further-resources/past-atar-course-exams/mathematics-specialist-past-atar-course-exams',
}

def existing_urls() -> set[str]:
    urls = set()
    for path in DATA.glob('*.csv'):
        if path in {OUTPUT, DATA / 'final_resources.csv'}:
            continue
        with path.open(newline='', encoding='utf-8') as handle:
            urls.update(row.get('resource_url', '').strip().lower() for row in csv.DictReader(handle) if row.get('resource_url'))
    return urls

def subject_for(filename: str) -> str:
    upper = filename.upper()
    if 'MAM' in upper:
        return 'MAM'
    if 'MAS' in upper:
        return 'MAS'
    raise ValueError(f'unknown SCSA subject: {filename}')

def year_for(filename: str) -> str:
    for year in ('2020', '2021'):
        if year in filename:
            return year
    raise ValueError(f'unknown year: {filename}')

def main() -> None:
    content = {row['file']: row for row in csv.DictReader(CONTENT_AUDIT.open(encoding='utf-8'))}
    duplicates = existing_urls()
    rows = []
    skipped = []
    for audit_row in csv.DictReader(URL_AUDIT.open(encoding='utf-8')):
        url = audit_row['resource_url'].strip()
        filename = Path(urlparse(url).path).name
        if not any(year in filename for year in ('2020', '2021')) or audit_row['included'] != 'Yes':
            continue
        if url.lower() in duplicates:
            skipped.append((url, 'active duplicate'))
            continue
        evidence = content.get(filename)
        if not evidence or evidence.get('substantive') != 'keep':
            skipped.append((url, 'no substantive keep evidence'))
            continue
        subject = subject_for(filename)
        year = year_for(filename)
        is_key = 'MARKING_KEY' in filename.upper() or 'MARKING-KEY' in filename.upper() or 'RATIFIED' in filename.upper() and 'EXAMINATION' not in filename.upper()
        label = 'marking key' if is_key else 'examination'
        rows.append({
            'country': 'Australia', 'track': 'EM',
            'topic_tags': 'mathematics;calculus;functions;probability;statistics;algebra;geometry;assessment;past year questions',
            'priority': 'A', 'source_type': 'State examination authority archive',
            'source_title': f"SCSA {'Mathematics Methods' if subject == 'MAM' else 'Mathematics Specialist'} past ATAR course exams (official)",
            'source_url': PAGES[subject], 'resource_title': f"SCSA {year} {'Mathematics Methods' if subject == 'MAM' else 'Mathematics Specialist'} — {label} ({'marking key' if is_key else 'exam'})",
            'resource_url': url, 'resource_class': 'Solution archive' if is_key else 'Exam paper', 'language': 'English',
            'notes': 'Official SCSA public English assessment document; substantive examination or marking-key PDF retained. Formula sheets and summary reports excluded.',
            'access_model': 'Free public web resource', 'verification_status': 'Item-level URL audit HTTP 200 + local PDF audit · verified 2026-08-16', 'free_resource': 'Yes'
        })
    if not rows:
        raise SystemExit('no eligible 2020–2021 SCSA rows')
    with OUTPUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS); writer.writeheader(); writer.writerows(rows)
    print(f'wrote {len(rows)} rows to {OUTPUT}; skipped {len(skipped)} candidates')
    for url, reason in skipped:
        print(f'skipped\t{reason}\t{url}')

if __name__ == '__main__':
    main()
