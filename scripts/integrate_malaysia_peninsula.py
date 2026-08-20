from pathlib import Path
import csv

OUT = Path('/home/ubuntu/ga-em-dm-resource-hub/client/src/data/malaysia_peninsula_dcs1123_verified_resources.csv')
AUDIT = Path('/home/ubuntu/ga-em-dm-resource-hub/research/malaysia_peninsula_clean_content_audit.csv')
HEADER = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
SOURCE_PAGE = 'https://digitallibrary.peninsulacollege.edu.my/'
RESOURCE_URL = 'https://digitallibrary.peninsulacollege.edu.my/bitstreams/034e0e9d-dd63-499d-b55f-7bb59d66d3c0/download'
row = ['Malaysia','DM','discrete mathematics;logic;sets;probability;graphs;relations;functions','A','Official college digital library','Peninsula College Georgetown Digital Library — DCS1123 Discrete Mathematics','https://digitallibrary.peninsulacollege.edu.my/','DCS1123 Discrete Mathematics — Final Examination — January 2026','https://digitallibrary.peninsulacollege.edu.my/bitstreams/034e0e9d-dd63-499d-b55f-7bb59d66d3c0/download','Official final examination question paper','English','Publicly retrievable four-question final examination; local extraction found substantive Boolean algebra, sets, probability, tree-diagram, and related discrete-mathematics questions. The paper is labelled CONFIDENTIAL by the college; no access control was bypassed and no answer key was inferred.','Free public PDF; no login observed','HTTP 200 · verified 2026-08-17','Yes']
OUT.write_text('', encoding='utf-8')
with OUT.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(HEADER); w.writerow(row)
AUDIT.write_text('filename,source_url,http_status,content_type,bytes,language,question_markers,decision,reason\npeninsula_dcs1123_exam_a.pdf,' + RESOURCE_URL + ',200,application/pdf,1015357,English,"Boolean algebra; sets; probability; tree diagram; logic; questions",KEEP,"Substantive four-question English Discrete Mathematics final examination; public repository content endpoint; no exact catalog URL duplicate"\n', encoding='utf-8')
print(OUT)
print(AUDIT)
