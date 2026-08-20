import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'client/src/data'
AUDIT = ROOT / 'research/australia_nesa_2014_mg_local_audit.csv'
OUT = DATA / 'australia_nesa_2014_mg_verified_resources.csv'
COLUMNS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']


def existing_urls():
    urls = set()
    for path in DATA.glob('*.csv'):
        if path in {OUT, DATA / 'final_resources.csv'}:
            continue
        with path.open(newline='', encoding='utf-8') as handle:
            urls.update(row.get('resource_url', '').strip().lower() for row in csv.DictReader(handle) if row.get('resource_url'))
    return urls


def title_and_class(kind: str):
    mapping = {
        'exam': ('examination paper', 'Exam paper'),
        'specimen exam': ('specimen examination paper', 'Practice paper'),
        'worked solutions': ('worked solutions', 'Solution archive'),
        'marking guidelines': ('marking guidelines', 'Solution archive'),
        'marking feedback': ('marking feedback', 'Solution archive'),
    }
    return mapping.get(kind, (kind, 'Exam paper'))


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
        title_kind, resource_class = title_and_class(audit['kind'])
        rows.append({
            'country': 'Australia',
            'track': 'EM',
            'topic_tags': 'mathematics;functions;probability;statistics;algebra;geometry;assessment;past year questions',
            'priority': 'A',
            'source_type': 'State examination authority archive',
            'source_title': 'NSW Education Standards Authority Mathematics General HSC archive (official)',
            'source_url': audit['page_url'],
            'resource_title': f"NSW NESA {audit['year']} Mathematics General — {title_kind}",
            'resource_url': url,
            'resource_class': resource_class,
            'language': 'English',
            'notes': 'Official NSW NESA public English Mathematics General assessment document; substantive questions, worked solutions, marking criteria, or feedback retained after browser verification and local text audit.',
            'access_model': 'Free public web resource',
            'verification_status': 'Browser fetch HTTP 200 + application/pdf + local substantive audit · verified 2026-08-16',
            'free_resource': 'Yes',
        })
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'wrote {len(rows)} rows to {OUT}')


if __name__ == '__main__':
    main()
