from pathlib import Path
import requests,csv,time
root=Path(__file__).resolve().parents[1]; out=root/'research'/'singapore_math_candidates'; out.mkdir(parents=True,exist_ok=True)
items=[
('nus_qualifying_paper_4_s1_2122','NUS Mathematics Qualifying Exam Paper 4 (S1 AY2021/2022)','https://www.math.nus.edu.sg/wp-content/uploads/sites/4/2024/07/Paper-4-S1-2122.pdf'),
('ntu_mqt_sample','NTU NIE Mathematics Qualifying Test sample questions','https://www.ntu.edu.sg/media/docs/nielibraries/academic-department/nie-mme/mqtsample.pdf?sfvrsn=d86403e5_3'),
]
with (out/'manifest.tsv').open('w',newline='',encoding='utf-8') as fh:
 w=csv.writer(fh,delimiter='\t'); w.writerow(['stem','title','url','status','content_type','bytes'])
 for stem,title,url in items:
  p=out/(stem+'.pdf')
  try:
   r=requests.get(url,timeout=30,headers={'User-Agent':'SignalAtlasResearch/1.0'}); p.write_bytes(r.content); w.writerow([stem,title,url,r.status_code,r.headers.get('content-type',''),len(r.content)]); print(stem,r.status_code,r.headers.get('content-type',''),len(r.content))
  except Exception as e: w.writerow([stem,title,url,'ERROR','',str(e)]); print(stem,'ERROR',e)
  time.sleep(.5)
