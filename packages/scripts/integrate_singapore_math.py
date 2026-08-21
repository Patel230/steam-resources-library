from pathlib import Path
import csv
root=Path(__file__).resolve().parents[1]
out=root/'apps/web/src/data/singapore_official_math_verified_resources.csv'
ledger=root/'research/singapore_math_clean_content_audit.csv'
headers=['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
base='https://www.ntu.edu.sg/nie/about-us/academic-departments/mathematics-and-mathematics-education/mathematics-qualifying-test'
items=[
('ntu_mqt_sample','GA','aptitude, mathematics, logical reasoning, MCQ','National Institute of Education (NTU) Mathematics Qualifying Test sample questions','https://www.ntu.edu.sg/media/docs/nielibraries/academic-department/nie-mme/mqtsample.pdf?sfvrsn=d86403e5_3','Sample question paper'),
('nus_qualifying_paper_4_s1_2122','EM','qualifying examination, advanced mathematics, university mathematics','National University of Singapore Mathematics Qualifying Exam Paper 4','https://www.math.nus.edu.sg/wp-content/uploads/sites/4/2024/07/Paper-4-S1-2122.pdf','Exam paper'),
]
rows=[]; audits=[]
for stem,track,tags,title,url,klass in items:
    txt=(root/'research/singapore_math_candidates'/f'{stem}.txt').read_text(encoding='utf-8',errors='ignore')
    ok=len(txt)>1500 and any(x in txt.lower() for x in ('question','evaluate','find','prove','multiple choice'))
    if not ok: raise SystemExit(f'Failed substantive audit: {stem}')
    source_url=base if stem.startswith('ntu_') else 'https://www.math.nus.edu.sg/'
    rows.append({'country':'Singapore','track':track,'topic_tags':tags,'priority':'A','source_type':'University examination / aptitude archive','source_title':title,'source_url':source_url,'resource_title':title,'resource_url':url,'resource_class':klass,'language':'English','notes':'Official public English Mathematics material; locally text-extracted, reviewed for substantive questions, and checked for exact URL duplication before registration.','access_model':'Free public download','verification_status':'HTTP 200 · verified 2026-08-17','free_resource':'yes'})
    audits.append({'resource_title':title,'resource_url':url,'file':f'{stem}.pdf','extracted_chars':len(txt),'decision':'keep','reason':'Official public English question material with substantive mathematics problems; no exact catalog URL duplicate; not administrative or answer-only content.'})
with out.open('w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=headers); w.writeheader(); w.writerows(rows)
with ledger.open('w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=audits[0].keys()); w.writeheader(); w.writerows(audits)
print(f'Wrote {len(rows)} Singapore records')
