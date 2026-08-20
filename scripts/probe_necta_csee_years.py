from pathlib import Path
import csv, requests
root=Path(__file__).resolve().parents[1]
out=root/'research'/'tanzania_necta_csee_probe.tsv'
rows=[]
for year in range(2015,2024):
    url=f'https://onlinesys.necta.go.tz/cira/csee/{year}/041_BASIC_MATHEMATICS.pdf'
    try:
        r=requests.get(url,timeout=6,headers={'User-Agent':'SignalAtlasResearch/1.0'},allow_redirects=True)
        rows.append([year,r.status_code,r.headers.get('content-type',''),len(r.content),r.url])
    except Exception as e:
        rows.append([year,'ERROR','',str(e),url])
with out.open('w',newline='',encoding='utf-8') as fh:
    w=csv.writer(fh,delimiter='\t'); w.writerow(['year','status','content_type','bytes_or_error','final_url']); w.writerows(rows)
print(out)
for row in rows: print('\t'.join(map(str,row)))
