import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data'
AUDIT = ROOT / 'research/australia_nesa_2020_2023_local_audit.csv'
OUT = DATA / 'australia_nesa_2020_2023_verified_resources.csv'
COLUMNS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']

def existing_urls():
    urls = set()
    for path in DATA.glob('*.csv'):
        if path in {OUT, DATA / 'final_resources.csv'}:
            continue
        with path.open(newline='', encoding='utf-8') as h:
            urls.update(r.get('resource_url', '').strip().lower() for r in csv.DictReader(h) if r.get('resource_url'))
    return urls

def main():
    dup = existing_urls(); rows = []
    for audit in csv.DictReader(AUDIT.open(encoding='utf-8')):
        if audit['substantive'] != 'keep':
            raise RuntimeError(f"audit did not keep {audit['key']}")
        url = audit['resource_url']
        if url.lower() in dup:
            print('DUPLICATE', url)
            continue
        kind = audit['kind']
        title_kind = 'marking guidelines' if kind == 'guide' else 'examination paper'
        rows.append({'country':'Australia','track':'EM','topic_tags':'mathematics;calculus;functions;probability;statistics;algebra;geometry;assessment;past year questions','priority':'A','source_type':'State examination authority archive','source_title':'NSW Education Standards Authority Mathematics Advanced HSC exam archive (official)','source_url':audit['page_url'],'resource_title':f"NSW NESA {audit['year']} Mathematics Advanced — {title_kind}",'resource_url':url,'resource_class':'Solution archive' if kind == 'guide' else 'Exam paper','language':'English','notes':'Official NSW NESA public English Mathematics Advanced HSC assessment document; substantive examination or marking-guideline PDF retained after browser download and local text audit.','access_model':'Free public web resource','verification_status':'Browser fetch HTTP 200 + application/pdf + local substantive audit · verified 2026-08-16','free_resource':'Yes'})
    with OUT.open('w', newline='', encoding='utf-8') as h:
        w = csv.DictWriter(h, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
    print(f'wrote {len(rows)} rows to {OUT}')

if __name__ == '__main__':
    main()
