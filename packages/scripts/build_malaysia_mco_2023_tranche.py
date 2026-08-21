import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data'
OUTPUT = DATA / 'malaysia_mco_2023_verified_resources.csv'
AUDIT = ROOT / 'research/malaysia_mco_2023_url_audit.csv'
SOURCE_URL = 'https://ioimalaysia.org/competition/mco/2023/'
VERIFY_DATE = '2026-08-16'

BROWSER_VERIFIED = [
    ('A', 'https://codeforces.com/group/IO0c6wbyI8/contest/431909/problem/A', 'Two Pointers (easy version)', 'Browser rendered substantive English statement with input, output, constraints, scoring, examples, and no login wall.'),
    ('B', 'https://codeforces.com/group/IO0c6wbyI8/contest/431909/problem/B', 'Love Letter', 'Browser rendered substantive English statement with input, output, constraints, scoring, examples, and no login wall.'),
    ('C', 'https://codeforces.com/group/IO0c6wbyI8/contest/431909/problem/C', 'Two Pointers (hard version)', 'Browser rendered substantive English statement with input, output, constraints, scoring, examples, and no login wall.'),
    ('D', 'https://codeforces.com/group/IO0c6wbyI8/contest/431909/problem/D', 'Segment Union', 'Browser rendered substantive English statement with input, output, constraints, scoring, examples, and no login wall.'),
]

FIELDS = ['country', 'track', 'topic_tags', 'priority', 'source_type', 'source_title', 'source_url', 'resource_title', 'resource_url', 'resource_class', 'language', 'notes', 'access_model', 'verification_status', 'free_resource']


def catalog_urls():
    urls = set()
    for path in DATA.glob('*.csv'):
        if path == OUTPUT:
            continue
        with path.open(newline='', encoding='utf-8') as handle:
            urls.update((row.get('resource_url') or '').strip() for row in csv.DictReader(handle))
    return urls


def main():
    existing = catalog_urls()
    rows = [item for item in BROWSER_VERIFIED if item[1] not in existing]
    with OUTPUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for letter, url, title, evidence in rows:
            writer.writerow({
                'country': 'Malaysia',
                'track': 'DM',
                'topic_tags': 'algorithms;competitive programming;discrete mathematics;informatics;contest;problem statement',
                'priority': 'A',
                'source_type': 'Official national computing olympiad task archive',
                'source_title': 'Malaysian Informatics and Programming Society (MIPS) — MCO 2023 direct tasks',
                'source_url': SOURCE_URL,
                'resource_title': f'MCO 2023 — Problem {letter}: {title}',
                'resource_url': url,
                'resource_class': 'Official MCO English problem statement',
                'language': 'English',
                'notes': f'Direct task in the public IOI Malaysia Codeforces group. {evidence} MIPS links the parent annual contest archive; browser verification is unauthenticated and the exact URL was absent from the active catalog at generation time.',
                'access_model': 'Free public web archive',
                'verification_status': f'HTTP 200 · verified {VERIFY_DATE}',
                'free_resource': 'Yes',
            })
    with AUDIT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['resource_url', 'title', 'parent_archive_linked_by_mips', 'browser_access', 'english_statement', 'duplicate_at_generation', 'included', 'verification_note'])
        for letter, url, title, evidence in BROWSER_VERIFIED:
            writer.writerow([url, f'MCO 2023 Problem {letter}: {title}', 'Yes', 'HTTP 200', 'Yes', 'No' if url not in existing else 'Yes', 'Yes' if url not in existing else 'No', evidence])
    print(f'Wrote {len(rows)} verified direct MCO 2023 task records to {OUTPUT}')


if __name__ == '__main__':
    main()
