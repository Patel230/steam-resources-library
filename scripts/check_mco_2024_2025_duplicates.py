import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'client/src/data'
CANDIDATES = [
    *[f'https://codeforces.com/group/IO0c6wbyI8/contest/606535/problem/{letter}' for letter in 'ABCD'],
    *[f'https://codeforces.com/group/IO0c6wbyI8/contest/105087/problem/{letter}' for letter in 'ABCD'],
]

existing = set()
for path in DATA.glob('*.csv'):
    with path.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            url = (row.get('resource_url') or '').strip()
            if url:
                existing.add(url)

for url in CANDIDATES:
    print(('DUPLICATE' if url in existing else 'NEW') + '\t' + url)
print(f'new={sum(url not in existing for url in CANDIDATES)} duplicate={sum(url in existing for url in CANDIDATES)}')
