from pathlib import Path
import csv
import re
import requests

src=Path(__file__).resolve().parents[1]/'research'/'japan_mext_math_links.tsv'
out=Path(__file__).resolve().parents[1]/'research'/'japan_mext_math_candidates'
out.mkdir(parents=True,exist_ok=True)
rows=[]
for i,line in enumerate(src.read_text(encoding='utf-8').splitlines(),1):
    label,url=line.split('\t',1)
    filename=url.rsplit('/',1)[-1]
    path=out/filename
    try:
        r=requests.get(url,timeout=30)
        path.write_bytes(r.content)
        rows.append({'index':i,'label':label,'url':url,'status':r.status_code,'content_type':r.headers.get('content-type',''),'bytes':len(r.content),'file':filename})
    except Exception as exc:
        rows.append({'index':i,'label':label,'url':url,'status':'ERROR','content_type':'','bytes':0,'file':filename,'error':str(exc)})
with (out/'download_manifest.csv').open('w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print(out)
