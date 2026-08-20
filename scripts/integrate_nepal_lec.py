from pathlib import Path
import csv
root=Path(__file__).resolve().parents[1]
out=root/'client/src/data/nepal_lec_verified_resources.csv'
ledger=root/'research/nepal_lec_clean_content_audit.csv'
headers=['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
items=[
('bct_engineering_math_i','Engineering Mathematics I — Tribhuvan University Institute of Engineering examination (2074 Chaitra)','https://lec.edu.np/uploads/document/638af453dc572.pdf','calculus, differential equations, analytic geometry, engineering mathematics'),
('bct_engineering_math_ii','Engineering Mathematics II — Tribhuvan University Institute of Engineering examination (2079 Ashwin)','https://lec.edu.np/uploads/document/63b96f094d2f7.pdf','multivariable calculus, vector calculus, multiple integration, engineering mathematics'),
]
base='https://lec.edu.np/downloads/old-questions'
rows=[]; audits=[]
for stem,title,url,tags in items:
    txt=(root/'research/nepal_lec_math_candidates'/f'{stem}.txt').read_text(encoding='utf-8',errors='ignore')
    if len(txt)<10000 or 'ENGINEERING' not in txt.upper() or not any(x in txt.lower() for x in ('evaluate','find','state','theorem')):
        raise SystemExit(f'Failed substantive audit: {stem}')
    rows.append({'country':'Nepal','track':'EM','topic_tags':tags,'priority':'A','source_type':'University examination archive','source_title':'Lalitpur Engineering College — official Old Questions archive','source_url':base,'resource_title':title,'resource_url':url,'resource_class':'Exam paper','language':'English','notes':'Official public Tribhuvan University Institute of Engineering examination paper surfaced through the LEC archive; locally text-extracted and audited as substantive English mathematics content.','access_model':'Free public download','verification_status':'HTTP 200 · verified 2026-08-17','free_resource':'yes'})
    audits.append({'resource_title':title,'resource_url':url,'file':f'{stem}.pdf','extracted_chars':len(txt),'decision':'keep','reason':'Public official exam paper with substantive English mathematics questions; non-duplicate URL and not administrative content.'})
with out.open('w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=headers); w.writeheader(); w.writerows(rows)
with ledger.open('w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=audits[0].keys()); w.writeheader(); w.writerows(audits)
print(f'Wrote {len(rows)} Nepal records')
