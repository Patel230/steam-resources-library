from collections import Counter
from pathlib import Path
import csv

counts=Counter()
for path in sorted((Path(__file__).resolve().parents[1]/'client'/'src'/'data').glob('*.csv')):
    with path.open(encoding='utf-8-sig', newline='') as fh:
        reader=csv.DictReader(fh)
        for row in reader:
            country=(row.get('country') or '').strip()
            if country:
                counts[country]+=1
for country,n in sorted(counts.items(), key=lambda item:(-item[1], item[0])):
    print(f'{country}\t{n}\t{max(0,100-n)}')
