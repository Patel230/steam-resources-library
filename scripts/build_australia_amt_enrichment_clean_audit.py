import csv
from pathlib import Path
ROOT=Path('/home/ubuntu/ga-em-dm-resource-hub'); src=ROOT/'research/australia_amt_enrichment_local_audit.csv'; out=ROOT/'research/clean_content_pdf_audit_australia_amt_enrichment_20260816.csv'
fields=['resource_url','decision','reason','evidence_source','text_chars','english_cues']
with src.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
with out.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
 for r in rows:
  warn=f" Extractor warning: {r['extractor_warning']}" if r['extractor_warning'] else ''
  w.writerow({'resource_url':r['resource_url'],'decision':r['decision'],'reason':r['reason']+warn,'evidence_source':f"{r['filename']} · {r['bytes']} bytes · HTTP {r['status']} · {r['text_chars']} extracted characters",'text_chars':r['text_chars'],'english_cues':r['english_cues']})
print(f'wrote {len(rows)} rows to {out}')
