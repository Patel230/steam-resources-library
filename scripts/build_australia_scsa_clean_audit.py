from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import unquote

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'client/src/data/australia_scsa_2022_2025_verified_resources.csv'
CONTENT = ROOT / 'research/australia_scsa_2022_2025_content_audit.csv'
OUT = ROOT / 'research/clean_content_pdf_audit_australia_scsa_20260816.csv'

def main() -> None:
    audit = {row['file']: row for row in csv.DictReader(CONTENT.open(encoding='utf-8'))}
    rows = []
    for row in csv.DictReader(DATA.open(encoding='utf-8')):
        filename = unquote(row['resource_url'].split('?', 1)[0].split('#', 1)[0].rstrip('/').rsplit('/', 1)[-1])
        evidence = audit.get(filename)
        if not evidence or evidence['substantive'] != 'keep':
            raise SystemExit(f'missing keep evidence for {filename}')
        rows.append({'resource_url': row['resource_url'].strip().lower(), 'decision': 'keep', 'characters': evidence['characters'], 'english_cues': evidence['english_cues'], 'evidence_file': filename})
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    print(f'wrote {len(rows)} recognized clean-content decisions to {OUT}')

if __name__ == '__main__': main()
