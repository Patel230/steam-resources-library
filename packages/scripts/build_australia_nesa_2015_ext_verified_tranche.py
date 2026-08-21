import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data'
AUDIT = ROOT / 'research/australia_nesa_2015_ext_local_audit.csv'
OUT = DATA / 'australia_nesa_2015_ext_verified_resources.csv'
COLUMNS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']


def existing_urls():
    urls = set()
    for path in DATA.glob('*.csv'):
        if path in {OUT, DATA / 'final_resources.csv'}:
            continue
        with path.open(newline='', encoding='utf-8') as handle:
            urls.update(row.get('resource_url', '').strip().lower() for row in csv.DictReader(handle) if row.get('resource_url'))
    return urls


def main():
    duplicates = existing_urls()
    rows = []
    for audit in csv.DictReader(AUDIT.open(newline='', encoding='utf-8')):
        if audit['substantive'] != 'keep':
            raise RuntimeError(f"audit did not keep {audit['key']}")
        url = audit['resource_url']
        if url.lower() in duplicates:
            print('DUPLICATE', url)
            continue
        course = audit['course']
        kind = audit['kind']
        title_kind = 'marking guidelines' if kind == 'marking guidelines' else ('marking feedback' if kind == 'marking feedback' else 'examination paper')
        rows.append({
            'country': 'Australia',
            'track': 'EM',
            'topic_tags': 'mathematics;calculus;complex numbers;proof;vectors;mechanics;assessment;past year questions',
            'priority': 'A',
            'source_type': 'State examination authority archive',
            'source_title': f'NSW Education Standards Authority {course} HSC archive (official)',
            'source_url': audit['page_url'],
            'resource_title': f"NSW NESA {audit['year']} {course} — {title_kind}",
            'resource_url': url,
            'resource_class': 'Solution archive' if kind != 'exam' else 'Exam paper',
            'language': 'English',
            'notes': 'Official NSW NESA public English Mathematics Extension assessment document; substantive examination questions, marking criteria, or marker feedback retained after browser source verification and local text audit. The Extension 1 exam PDF emitted a pdftotext trailer warning, but still yielded substantive extracted question text and was retained with that evidence recorded in the audit ledger.',
            'access_model': 'Free public web resource',
            'verification_status': 'Browser source HTTP 200 + application/pdf + local substantive audit · verified 2026-08-16',
            'free_resource': 'Yes',
        })
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'wrote {len(rows)} rows to {OUT}')


if __name__ == '__main__':
    main()
