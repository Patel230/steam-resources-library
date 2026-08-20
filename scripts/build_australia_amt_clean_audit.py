import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
LOCAL = ROOT / 'research/australia_amt_local_audit.csv'
OUT = ROOT / 'research/clean_content_pdf_audit_australia_amt_20260816.csv'
FIELDS = ['resource_url', 'decision', 'reason', 'evidence_source', 'text_chars', 'english_cues']

with LOCAL.open(newline='', encoding='utf-8') as handle:
    rows = list(csv.DictReader(handle))
with OUT.open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS); writer.writeheader()
    for row in rows:
        warning = f" Extractor warning: {row['extractor_warning']}" if row['extractor_warning'] else ''
        writer.writerow({
            'resource_url': row['resource_url'], 'decision': row['substantive'],
            'reason': row['reason'] + warning,
            'evidence_source': f"{row['filename']} · {row['bytes']} bytes · HTTP {row['status']} · {row['text_chars']} extracted characters",
            'text_chars': row['text_chars'], 'english_cues': row['english_cues'],
        })
print(f'wrote {len(rows)} clean-content audit rows to {OUT}')
