from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data'
AUDIT = ROOT / 'research/australia_qcaa_2023_2025_local_audit.csv'
OUT = DATA / 'australia_qcaa_2023_2025_verified_resources.csv'
COLS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']

def existing_urls() -> set[str]:
    seen: set[str] = set()
    for path in DATA.glob('*.csv'):
        if path.name in {OUT.name, 'final_resources.csv'}:
            continue
        with path.open(newline='', encoding='utf-8') as handle:
            seen.update(row.get('resource_url','').strip().lower() for row in csv.DictReader(handle) if row.get('resource_url'))
    return seen

def resource_class(title: str) -> str:
    lower = title.lower()
    if 'marking guide' in lower:
        return 'Solutions'
    if 'multiple-choice' in lower:
        return 'MCQ'
    return 'Exam'

def main() -> None:
    known = existing_urls(); rows=[]
    with AUDIT.open(newline='', encoding='utf-8') as handle:
        for audit in csv.DictReader(handle):
            if audit['decision'] != 'keep':
                raise RuntimeError(f"Audit did not keep {audit['key']}: {audit['reason']}")
            url = audit['resource_url'].strip().lower()
            if url in known:
                print('DUPLICATE', audit['resource_url'])
                continue
            rows.append({
                'country':'Australia','track':'EM',
                'topic_tags':'general mathematics;probability;statistics;sequences;graphs;networks;multiple choice',
                'priority':'A','source_type':'Queensland Curriculum and Assessment Authority archive',
                'source_title':'QCAA General Mathematics syllabus and external assessment archive (official)',
                'source_url':audit['page_url'],'resource_title':audit['title'],'resource_url':audit['resource_url'],
                'resource_class':resource_class(audit['title']),'language':'English',
                'notes':'Official QCAA external-assessment question, response, or marking-guide PDF retained after direct browser verification, local substantive English-content audit, and exact URL deduplication. Public access does not require QCAA Portal login.',
                'access_model':'Free public web resource',
                'verification_status':'Official source HTTP 200 + browser download + local substantive audit · verified 2026-08-16',
                'free_resource':'Yes'
            })
    with OUT.open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=COLS); writer.writeheader(); writer.writerows(rows)
    print(f'Wrote {len(rows)} new rows to {OUT}')

if __name__=='__main__': main()
