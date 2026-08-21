from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path('/home/ubuntu/ga-em-dm-resource-hub'); DATA=ROOT/'apps/web/src/data'
AUDIT=ROOT/'research/australia_vcaa_2023_2025_local_audit.csv'; OUT=DATA/'australia_vcaa_2023_2025_verified_resources.csv'
COLS=['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']

def existing_urls()->set[str]:
    seen=set()
    for p in DATA.glob('*.csv'):
        if p.name in {OUT.name,'final_resources.csv'}: continue
        with p.open(newline='',encoding='utf-8') as h: seen.update(r.get('resource_url','').strip().lower() for r in csv.DictReader(h) if r.get('resource_url'))
    return seen

def main()->None:
    known=existing_urls(); rows=[]
    with AUDIT.open(newline='',encoding='utf-8') as h:
        for a in csv.DictReader(h):
            if a['decision']!='keep': continue
            url=a['resource_url'].strip().lower()
            if url in known: print('DUPLICATE',a['resource_url']); continue
            title=a['title']; cls='Solutions' if 'marking' in title.lower() or 'response' in title.lower() else 'Exam'
            rows.append({'country':'Australia','track':'EM','topic_tags':'general mathematics;data analysis;financial mathematics;networks;matrices;probability;statistics','priority':'A','source_type':'Victorian Curriculum and Assessment Authority archive','source_title':'VCAA General Mathematics examination and external-assessment archive (official)','source_url':a['page_url'],'resource_title':title,'resource_url':a['resource_url'],'resource_class':cls,'language':'English','notes':'Official VCAA General Mathematics examination or marking-guidelines/sample-responses PDF retained after public source verification, local substantive English-content audit, and exact URL deduplication. Non-text-extractable 2024 exam scans are excluded under the clean-content evidence policy.','access_model':'Free public web resource','verification_status':'Official source HTTP 200 + local substantive audit · verified 2026-08-16','free_resource':'Yes'})
    with OUT.open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=COLS); w.writeheader(); w.writerows(rows)
    print(f'Wrote {len(rows)} new rows to {OUT}')

if __name__=='__main__': main()
