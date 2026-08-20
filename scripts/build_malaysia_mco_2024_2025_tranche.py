import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'client/src/data'
OUTPUT = DATA / 'malaysia_mco_2024_2025_verified_resources.csv'
AUDIT = ROOT / 'research/malaysia_mco_2024_2025_url_audit.csv'
SOURCE_URL = 'https://ioimalaysia.org/resource/for-student/practice/'
VERIFY_DATE = '2026-08-16'

BROWSER_VERIFIED = [
    ('MCO 2025', 'A', 'https://codeforces.com/group/IO0c6wbyI8/contest/606535/problem/A', 'Long Binary String', 'Browser rendered the English statement with input, output, constraints, scoring, and examples without login.'),
    ('MCO 2025', 'B', 'https://codeforces.com/group/IO0c6wbyI8/contest/606535/problem/B', 'Rectangle Connections', 'Browser rendered the English statement with input, output, constraints, scoring, and examples without login.'),
    ('MCO 2025', 'C', 'https://codeforces.com/group/IO0c6wbyI8/contest/606535/problem/C', 'Subsequence', 'Browser rendered the English statement with input, output, constraints, scoring, and examples without login.'),
    ('MCO 2025', 'D', 'https://codeforces.com/group/IO0c6wbyI8/contest/606535/problem/D', 'GCD Equality', 'Browser rendered the English statement with input, output, constraints, scoring, and examples without login.'),
    ('MCO 2024', 'A', 'https://codeforces.com/group/IO0c6wbyI8/contest/105087/problem/A', 'Dragon Attack', 'Browser rendered the English statement with input, output, constraints, scoring, and examples without login.'),
    ('MCO 2024', 'B', 'https://codeforces.com/group/IO0c6wbyI8/contest/105087/problem/B', 'Max Partition', 'Browser rendered the English statement with input, output, constraints, and examples without login.'),
    ('MCO 2024', 'C', 'https://codeforces.com/group/IO0c6wbyI8/contest/105087/problem/C', 'Escape', 'Browser rendered the English statement with full description, input, output, constraints, scoring, and example without login.'),
    ('MCO 2024', 'D', 'https://codeforces.com/group/IO0c6wbyI8/contest/105087/problem/D', 'Knights', 'Browser rendered the English statement with input, output, constraints, and scoring without login.'),
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
    rows = [item for item in BROWSER_VERIFIED if item[2] not in existing]
    with OUTPUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for year, letter, url, title, evidence in rows:
            writer.writerow({
                'country': 'Malaysia',
                'track': 'DM',
                'topic_tags': 'algorithms;competitive programming;discrete mathematics;informatics;contest;problem statement',
                'priority': 'A',
                'source_type': 'Official national computing olympiad task archive',
                'source_title': 'Malaysian Informatics and Programming Society (MIPS) — MCO direct tasks',
                'source_url': SOURCE_URL,
                'resource_title': f'{year} — Problem {letter}: {title}',
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
        for year, letter, url, title, evidence in BROWSER_VERIFIED:
            writer.writerow([url, f'{year} Problem {letter}: {title}', 'Yes', 'HTTP 200', 'Yes', 'No' if url not in existing else 'Yes', 'Yes' if url not in existing else 'No', evidence])
    print(f'Wrote {len(rows)} verified direct MCO task records to {OUTPUT}')


if __name__ == '__main__':
    main()
