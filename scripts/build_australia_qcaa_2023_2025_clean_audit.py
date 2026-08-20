from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
SOURCE = ROOT / 'research/australia_qcaa_2023_2025_local_audit.csv'
OUT = ROOT / 'research/clean_content_pdf_audit_australia_qcaa_2023_2025.csv'
FIELDS = ['resource_url','decision','title','pdf_text_chars','english_cues','substantive_cues','parser_warning','evidence']

def main() -> None:
    rows=[]
    with SOURCE.open(newline='',encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            if row['decision'] != 'keep':
                continue
            rows.append({k: row[k] for k in FIELDS[:-1]} | {'evidence':row['reason']})
    with OUT.open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    print(f'Wrote {len(rows)} clean-audit rows to {OUT}')

if __name__=='__main__': main()
