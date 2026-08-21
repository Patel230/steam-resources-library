from pathlib import Path
import requests, csv, time
root=Path(__file__).resolve().parents[1]
out=root/'research'/'nepal_lec_math_candidates'; out.mkdir(parents=True,exist_ok=True)
items=[
('bct_engineering_math_i','Engineering Math I','https://lec.edu.np/uploads/document/638af453dc572.pdf'),
('bct_engineering_math_ii','Engineering Math II','https://lec.edu.np/uploads/document/63b96f094d2f7.pdf'),
('bct_engineering_math_iii','Engineering Math III','https://lec.edu.np/uploads/document/63888d6c3cee6.pdf'),
('bce_applied_mathematics','Applied Mathematics','https://lec.edu.np/uploads/document/63b9730a4d36e.pdf'),
('bce_numerical_method','Numerical Method','https://lec.edu.np/uploads/document/63b9737c79c85.pdf'),
('bce_probability_statistics','Probability and Statistics','https://lec.edu.np/uploads/document/63905e6f3c53d.pdf'),
('bca_mathematics_i','Mathematics I','https://lec.edu.np/uploads/document/67b8398554e92.pdf'),
('bca_probability_statistics','Probability and Statistics','https://lec.edu.np/uploads/document/67b83942b61bc.pdf'),
]
with (out/'manifest.tsv').open('w',encoding='utf-8',newline='') as fh:
    w=csv.writer(fh,delimiter='\t'); w.writerow(['stem','title','url','status','content_type','bytes'])
    for stem,title,url in items:
        p=out/(stem+'.pdf')
        try:
            r=requests.get(url,timeout=15,headers={'User-Agent':'SignalAtlasResearch/1.0'}); p.write_bytes(r.content)
            w.writerow([stem,title,url,r.status_code,r.headers.get('content-type',''),len(r.content)])
            print(stem,r.status_code,r.headers.get('content-type',''),len(r.content))
        except Exception as e:
            w.writerow([stem,title,url,'ERROR','',str(e)]); print(stem,'ERROR',e)
        time.sleep(.3)
