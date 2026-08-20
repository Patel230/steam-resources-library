import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'client/src/data'
AUDIT = ROOT / 'research/australia_amt_local_audit.csv'
OUT = DATA / 'australia_amt_verified_resources.csv'
COLUMNS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']


def existing_urls():
    urls = set()
    for path in DATA.glob('*.csv'):
        if path.name == OUT.name or path.name == 'final_resources.csv':
            continue
        with path.open(newline='', encoding='utf-8') as handle:
            urls.update(row.get('resource_url', '').strip().lower() for row in csv.DictReader(handle) if row.get('resource_url'))
    return urls


def main():
    known = existing_urls(); rows = []
    for audit in csv.DictReader(AUDIT.open(newline='', encoding='utf-8')):
        if audit['substantive'] != 'keep':
            raise RuntimeError(f"audit did not keep {audit['key']}")
        url = audit['resource_url']
        if url.lower() in known:
            print('DUPLICATE', url); continue
        kind = 'Olympiad problem and solution set' if audit['kind'] == 'Olympiad' else 'Practice problem and solution set'
        rows.append({
            'country':'Australia', 'track':'DM',
            'topic_tags':'mathematics;problem solving;olympiad;combinatorics;geometry;number theory;probability;practice questions;solutions',
            'priority':'A', 'source_type':'Australian Maths Trust archive',
            'source_title':'Australian Maths Trust Past Papers Archives (official)',
            'source_url':audit['page_url'], 'resource_title':f"Australian Maths Trust — {audit['title']}",
            'resource_url':url, 'resource_class':'Olympiad' if audit['kind'] == 'Olympiad' else 'Quiz',
            'language':'English',
            'notes':'Official Australian Maths Trust free public English problem-and-solution PDF retained after HTTP 200 source verification, local substantive-content audit, and exact URL deduplication. Parser warnings, where present, are preserved in the research audit manifest.',
            'access_model':'Free public web resource',
            'verification_status':'Official source HTTP 200 + local substantive audit · verified 2026-08-16',
            'free_resource':'Yes',
        })
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS); writer.writeheader(); writer.writerows(rows)
    print(f'wrote {len(rows)} rows to {OUT}')

if __name__ == '__main__': main()
