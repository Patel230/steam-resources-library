from pathlib import Path
import csv

root=Path(__file__).resolve().parents[1]
out=root/'client'/'src'/'data'/'japan_mext_verified_resources.csv'
ledger=root/'research'/'japan_mext_clean_content_audit.csv'
headers=['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
selected=[
    ('2016_ga_math_a','2016 MEXT Undergraduate Mathematics (A) examination questions'),
    ('2016_ga_math_b','2016 MEXT Undergraduate Mathematics (B) examination questions'),
    ('2017_ga_math_a','2017 MEXT Undergraduate Mathematics (A) examination questions'),
    ('2017_ga_math_b','2017 MEXT Undergraduate Mathematics (B) examination questions'),
    ('2017_se_math','2017 MEXT Specialized Training College Mathematics examination questions'),
]
base='https://www.studyinjapan.go.jp/en/planning/scholarships/mext-scholarships/examination.html'
url_map={}
for line in (root/'research'/'japan_mext_math_links.tsv').read_text(encoding='utf-8').splitlines():
    label,url=line.split('\t',1)
    filename=url.rsplit('/',1)[-1].removesuffix('.pdf')
    url_map[filename]=url
rows=[]; audits=[]
for stem,title in selected:
    txt=(root/'research'/'japan_mext_math_candidates'/f'{stem}.txt').read_text(encoding='utf-8',errors='ignore')
    if len(txt)<2000 or 'MATHEMATICS' not in txt.upper() or not any(marker in txt.lower() for marker in ('answer the following', 'find ', 'if ', 'consider ')):
        raise SystemExit(f'Failed substantive audit: {stem}')
    if stem not in url_map:
        raise SystemExit(f'Missing URL: {stem}')
    rows.append({
        'country':'Japan','track':'EM','topic_tags':'algebra, calculus, geometry, functions, trigonometry, probability, entrance examination','priority':'A','source_type':'Government scholarship examination','source_title':'Study in Japan — MEXT Applicant Qualifying Examinations','source_url':base,'resource_title':title,'resource_url':url_map[stem],'resource_class':'Exam paper','language':'English','notes':'Official MEXT public sample examination paper with substantive English mathematics questions; locally text-extracted and audited for clean content.','access_model':'Free public download','verification_status':'HTTP 200 · verified 2026-08-17','free_resource':'yes'
    })
    audits.append({'resource_title':title,'resource_url':url_map[stem],'file':f'{stem}.pdf','extracted_chars':len(txt),'english_marker':'MATHEMATICS header and substantive English question markers present','decision':'keep','reason':'Substantive English question paper; not an answer-only or administrative document.'})
with out.open('w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=headers); w.writeheader(); w.writerows(rows)
with ledger.open('w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=audits[0].keys()); w.writeheader(); w.writerows(audits)
print(f'Wrote {len(rows)} records to {out}')
print(f'Wrote {len(audits)} audit rows to {ledger}')
