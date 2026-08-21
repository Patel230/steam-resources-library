import csv
from pathlib import Path
ROOT=Path('/home/ubuntu/ga-em-dm-resource-hub'); DATA=ROOT/'apps/web/src/data'; AUDIT=ROOT/'research/australia_amt_enrichment_local_audit.csv'; OUT=DATA/'australia_amt_enrichment_verified_resources.csv'
COLS=['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
def existing():
 urls=set()
 for p in DATA.glob('*.csv'):
  if p.name in {OUT.name,'final_resources.csv'}: continue
  with p.open(newline='',encoding='utf-8') as f: urls.update(r['resource_url'].strip().lower() for r in csv.DictReader(f) if r.get('resource_url'))
 return urls
def main():
 known=existing(); rows=[]
 for a in csv.DictReader(AUDIT.open(newline='',encoding='utf-8')):
  if a['decision']!='keep': raise RuntimeError(a['key'])
  if a['resource_url'].lower() in known: print('DUPLICATE',a['resource_url']); continue
  rows.append({'country':'Australia','track':'DM','topic_tags':'mathematics;problem solving;logic;number theory;combinatorics;geometry;proof;enrichment','priority':'A','source_type':'Australian Maths Trust archive','source_title':'Australian Maths Trust Free Activities archive (official)','source_url':a['page_url'],'resource_title':f"Australian Maths Trust — {a['title']}",'resource_url':a['resource_url'],'resource_class':'Assignment','language':'English','notes':'Official AMT free-activities sample PDF retained after HTTP 200, local substantive English-content audit, and exact URL deduplication. The page identifies these sample materials as free; paid program and shop routes are excluded. Parser warnings are preserved in the research audit manifest.','access_model':'Free public web resource','verification_status':'Official source HTTP 200 + local substantive audit · verified 2026-08-16','free_resource':'Yes'})
 with OUT.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=COLS); w.writeheader(); w.writerows(rows)
 print('wrote',len(rows),'rows to',OUT)
if __name__=='__main__': main()
