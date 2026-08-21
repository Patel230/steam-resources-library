import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data'
CANDIDATES = [f'https://codeforces.com/group/IO0c6wbyI8/contest/431909/problem/{letter}' for letter in 'ABCD']
existing = set()
for path in DATA.glob('*.csv'):
    with path.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            existing.add((row.get('resource_url') or '').strip().lower())
for url in CANDIDATES:
    print(f'{url}\t{"DUPLICATE" if url.lower() in existing else "NEW"}')
