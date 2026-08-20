from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path('/home/ubuntu/ga-em-dm-resource-hub')
SOURCE=ROOT/'research/australia_vcaa_2023_2025_local_audit.csv'
OUT=ROOT/'research/clean_content_pdf_audit_australia_vcaa_2023_2025.csv'
FIELDS=['resource_url','decision','title','pdf_text_chars','english_cues','substantive_cues','parser_warning','evidence']

def main()->None:
    rows=[]
    with SOURCE.open(newline='',encoding='utf-8') as h:
        for r in csv.DictReader(h):
            if r['decision']!='keep': continue
            rows.append({'resource_url':r['resource_url'],'decision':r['decision'],'title':r['title'],'pdf_text_chars':r['pdf_text_chars'],'english_cues':r['english_cues'],'substantive_cues':r['substantive_cues'],'parser_warning':r['parser_warning'],'evidence':r['reason']})
    with OUT.open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    print(f'Wrote {len(rows)} clean-audit rows to {OUT}')

if __name__=='__main__': main()
