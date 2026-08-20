from pathlib import Path
import csv, requests
root=Path(__file__).resolve().parents[1]; out=root/'research'/'tanzania_necta_candidates'; out.mkdir(parents=True,exist_ok=True)
items=[
('necta_csee_2015_basic_math','NECTA CSEE 2015 Basic Mathematics','https://onlinesys.necta.go.tz/cira/csee/2015/041_BASIC_MATHEMATICS.pdf'),
('necta_psle_2021_math','NECTA PSLE 2021 Mathematics','https://onlinesys.necta.go.tz/cira/psle/2021/04E_MATHEMATICS.pdf'),
]
with (out/'manifest.tsv').open('w',newline='',encoding='utf-8') as fh:
 w=csv.writer(fh,delimiter='\t'); w.writerow(['stem','title','url','status','content_type','bytes'])
 for stem,title,url in items:
  try:
   r=requests.get(url,timeout=20,headers={'User-Agent':'SignalAtlasResearch/1.0'}); (out/(stem+'.pdf')).write_bytes(r.content); print(stem,r.status_code,r.headers.get('content-type',''),len(r.content)); w.writerow([stem,title,url,r.status_code,r.headers.get('content-type',''),len(r.content)])
  except Exception as e: print(stem,'ERROR',e); w.writerow([stem,title,url,'ERROR','',str(e)])
