from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

DOWNLOADS = Path('/home/ubuntu/Downloads')
OUT = Path('/home/ubuntu/ga-em-dm-resource-hub/research/australia_scsa_2022_2025_content_audit.csv')

def main() -> None:
    files = sorted(p for p in DOWNLOADS.glob('*.PDF') if re.match(r'^202[2-5]-MA[MS]-', p.name) and '(1)' not in p.name)
    rows = []
    for path in files:
        result = subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True, check=False)
        text = result.stdout
        lower = text.lower()
        english_cues = sum(lower.count(word) for word in ('question', 'answer', 'mark', 'mathematics', 'calculator', 'examination'))
        substantive = len(text.strip()) >= 500 and english_cues >= 3
        rows.append({'file': path.name, 'bytes': path.stat().st_size, 'pdftotext_returncode': result.returncode, 'characters': len(text.strip()), 'english_cues': english_cues, 'substantive': 'keep' if substantive else 'review', 'sample': re.sub(r'\s+', ' ', text[:240]).strip()})
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else ['file'])
        writer.writeheader()
        writer.writerows(rows)
    keeps = sum(row['substantive'] == 'keep' for row in rows)
    print(f'files={len(rows)} keep={keeps} review={len(rows)-keeps} output={OUT}')
    for row in rows:
        print(row['file'], row['characters'], row['english_cues'], row['substantive'])

if __name__ == '__main__':
    main()
