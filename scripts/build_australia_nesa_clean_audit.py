import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
source = ROOT / 'research/australia_nesa_2020_2023_local_audit.csv'
out = ROOT / 'research/clean_content_pdf_audit_australia_nesa_20260816.csv'
with source.open(newline='', encoding='utf-8') as handle:
    rows = list(csv.DictReader(handle))
with out.open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=['resource_url', 'decision', 'reason'])
    writer.writeheader()
    for row in rows:
        writer.writerow({'resource_url': row['resource_url'], 'decision': 'keep' if row['substantive'] == 'keep' else 'review', 'reason': row['reason']})
print(f'wrote {len(rows)} recognized audit rows to {out}')
