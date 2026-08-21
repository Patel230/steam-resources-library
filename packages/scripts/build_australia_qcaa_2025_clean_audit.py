from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
SOURCE = ROOT / 'research/australia_qcaa_2025_local_audit.csv'
OUT = ROOT / 'research/clean_content_pdf_audit_australia_qcaa_2025.csv'
FIELDS = ['resource_url','decision','title','pdf_text_chars','english_cues','substantive_cues','parser_warning','evidence']

def main() -> None:
    rows = []
    with SOURCE.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            if row['decision'] != 'keep':
                continue
            rows.append({
                'resource_url': row['resource_url'],
                'decision': row['decision'],
                'title': row['title'],
                'pdf_text_chars': row['pdf_text_chars'],
                'english_cues': row['english_cues'],
                'substantive_cues': row['substantive_cues'],
                'parser_warning': row['parser_warning'],
                'evidence': row['reason'],
            })
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} clean-audit rows to {OUT}')

if __name__ == '__main__':
    main()
