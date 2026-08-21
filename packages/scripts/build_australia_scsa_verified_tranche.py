from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data'
OUTPUT = DATA / 'australia_scsa_2022_2025_verified_resources.csv'
AUDIT = ROOT / 'research/australia_scsa_2022_2025_content_audit.csv'
COLUMNS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
BASE = 'https://senior-secondary.scsa.wa.edu.au/__data/assets/pdf_file/'
PAGE = {
'MAM':'https://senior-secondary.scsa.wa.edu.au/further-resources/past-atar-course-exams/mathematics-methods-past-atar-course-exams',
'MAS':'https://senior-secondary.scsa.wa.edu.au/further-resources/past-atar-course-exams/mathematics-specialist-past-atar-course-exams',
}
ITEMS = [
('MAM','2025','key-assumed','0014/1231124/2025-MAM-Ratified-Calc-Assumed-Marking-Key.PDF','2025-MAM-Ratified-Calc-Assumed-Marking-Key.PDF'),('MAM','2025','key-free','0015/1231125/2025-MAM-Ratified-Calc-Free-Marking-Key.PDF','2025-MAM-Ratified-Calc-Free-Marking-Key.PDF'),('MAM','2025','exam-assumed','0012/1231122/2025-MAM-Examination-Calculator-Assumed.PDF','2025-MAM-Examination-Calculator-Assumed.PDF'),('MAM','2025','exam-free','0013/1231123/2025-MAM-Examination-Calculator-Free.PDF','2025-MAM-Examination-Calculator-Free.PDF'),
('MAM','2024','key-assumed','0009/1169532/2024-MAM-Ratified-Calc-Assumed-Marking-Key-Web-Version.PDF','2024-MAM-Ratified-Calc-Assumed-Marking-Key-Web-Version.PDF'),('MAM','2024','key-free','0010/1169533/2024-MAM-Ratified-Calc-Free-Marking-Key-Web-Version.PDF','2024-MAM-Ratified-Calc-Free-Marking-Key-Web-Version.PDF'),('MAM','2024','exam-assumed','0006/1169529/2024-MAM-Examination-Calculator-Assumed-Web-Version.PDF','2024-MAM-Examination-Calculator-Assumed-Web-Version.PDF'),('MAM','2024','exam-free','0008/1169531/2024-MAM-Examination-Calculator-Free-Web-Version.PDF','2024-MAM-Examination-Calculator-Free-Web-Version.PDF'),
('MAM','2023','exam-assumed','0004/1091560/2023-MAM-Examination-Calculator-Assumed.PDF','2023-MAM-Examination-Calculator-Assumed.PDF'),('MAM','2023','key-assumed','0007/1091563/2023-MAM-Ratified-Marking-Key-Calculator-Assumed.PDF','2023-MAM-Ratified-Marking-Key-Calculator-Assumed.PDF'),('MAM','2023','exam-free','0005/1091561/2023-MAM-Examination-Calculator-Free.PDF','2023-MAM-Examination-Calculator-Free.PDF'),('MAM','2023','key-free','0006/1091562/2023-MAM-Ratified-Marking-Key-Calculator-Free.PDF','2023-MAM-Ratified-Marking-Key-Calculator-Free.PDF'),
('MAM','2022','exam-assumed','0006/1042359/2022-MAM-Examination-Calculator-Assumed.PDF','2022-MAM-Examination-Calculator-Assumed.PDF'),('MAM','2022','key-assumed','0016/1042360/2022-MAM-Ratified-Calc-Assumed-Marking-Key.PDF','2022-MAM-Ratified-Calc-Assumed-Marking-Key.PDF'),('MAM','2022','exam-free','0017/1042361/2022-MAM-Examination-Calculator-Free.PDF','2022-MAM-Examination-Calculator-Free.PDF'),('MAM','2022','key-free','0018/1042362/2022-MAM-Ratified-Calc-Free-Marking-Key.PDF','2022-MAM-Ratified-Calc-Free-Marking-Key.PDF'),
('MAS','2025','key-assumed','0012/1231131/2025-MAS-Ratified-Calc-Assumed-Marking-Key.PDF','2025-MAS-Ratified-Calc-Assumed-Marking-Key.PDF'),('MAS','2025','key-free','0013/1231132/2025-MAS-Ratified-Calc-Free-Marking-Key.PDF','2025-MAS-Ratified-Calc-Free-Marking-Key.PDF'),('MAS','2025','exam-assumed','0019/1231129/2025-MAS-Examination-Calculator-Assumed.PDF','2025-MAS-Examination-Calculator-Assumed.PDF'),('MAS','2025','exam-free','0011/1231130/2025-MAS-Examination-Calculator-Free.PDF','2025-MAS-Examination-Calculator-Free.PDF'),
('MAS','2024','exam-assumed','0006/1171473/2024-MAS-Examination-Calculator-Assumed-Web-Version.PDF','2024-MAS-Examination-Calculator-Assumed-Web-Version.PDF'),('MAS','2024','exam-free','0007/1171474/2024-MAS-Examination-Calculator-Free-Web-Version.PDF','2024-MAS-Examination-Calculator-Free-Web-Version.PDF'),('MAS','2024','key-assumed','0008/1171475/2024-MAS-Ratified-Calc-Assumed-Marking-Key-Web-Version.PDF','2024-MAS-Ratified-Calc-Assumed-Marking-Key-Web-Version.PDF'),('MAS','2024','key-free','0009/1171476/2024-MAS-Ratified-Calc-Free-Marking-Key-Web-Version.PDF','2024-MAS-Ratified-Calc-Free-Marking-Key-Web-Version.PDF'),
('MAS','2023','exam-assumed','0004/1092739/2023-MAS-Examination-Calculator-Assumed.PDF','2023-MAS-Examination-Calculator-Assumed.PDF'),('MAS','2023','key-assumed','0006/1092741/2023-MAS-Ratified-Marking-Key-Calculator-Assumed.PDF','2023-MAS-Ratified-Marking-Key-Calculator-Assumed.PDF'),('MAS','2023','exam-free','0005/1092740/2023-MAS-Examination-Calculator-Free.PDF','2023-MAS-Examination-Calculator-Free.PDF'),('MAS','2023','key-free','0007/1092742/2023-MAS-Ratified-Marking-Key-Calculator-Free.PDF','2023-MAS-Ratified-Marking-Key-Calculator-Free.PDF'),
('MAS','2022','exam-assumed','0006/1042368/2022-MAS-Examination-Calculator-Assumed.PDF','2022-MAS-Examination-Calculator-Assumed.PDF'),('MAS','2022','key-assumed','0007/1042369/2022-MAS-Calc-Assumed-Ratified-Marking-Key.PDF','2022-MAS-Calc-Assumed-Ratified-Marking-Key.PDF'),('MAS','2022','exam-free','0017/1042370/2022-MAS-Examination_Calculator-Free.PDF','2022-MAS-Examination_Calculator-Free.PDF'),('MAS','2022','key-free','0018/1042371/2022-MAS-Calc-Free-Ratified-Marking-Key.PDF','2022-MAS-Calc-Free-Ratified-Marking-Key.PDF'),
]

def existing_urls():
    urls=set()
    for path in DATA.glob('*.csv'):
        if path in {OUTPUT, DATA/'final_resources.csv'}: continue
        with path.open(newline='',encoding='utf-8') as h: urls.update(r.get('resource_url','').strip().lower() for r in csv.DictReader(h) if r.get('resource_url'))
    return urls

def main():
    audit={r['file']:r for r in csv.DictReader(AUDIT.open(encoding='utf-8'))}
    dup=existing_urls(); rows=[]
    for subject,year,kind,path,filename in ITEMS:
        url=BASE+path
        if url.lower() in dup: raise RuntimeError(f'duplicate active URL: {url}')
        if audit.get(filename,{}).get('substantive')!='keep': raise RuntimeError(f'no local keep evidence: {filename}')
        label='marking key' if kind.startswith('key') else 'examination'
        rows.append({'country':'Australia','track':'EM','topic_tags':'mathematics;calculus;functions;probability;statistics;algebra;geometry;assessment;past year questions','priority':'A','source_type':'State examination authority archive','source_title':f"SCSA {'Mathematics Methods' if subject=='MAM' else 'Mathematics Specialist'} past ATAR course exams (official)",'source_url':PAGE[subject],'resource_title':f"SCSA {year} {'Mathematics Methods' if subject=='MAM' else 'Mathematics Specialist'} — {label} ({kind.replace('-', ' ')})",'resource_url':url,'resource_class':'Solution archive' if kind.startswith('key') else 'Exam paper','language':'English','notes':'Official SCSA public English assessment document; substantive examination or marking-key PDF retained. Formula sheets and summary reports excluded.','access_model':'Free public web resource','verification_status':'Browser HTTP 200 + local PDF audit · verified 2026-08-16','free_resource':'Yes'})
    with OUTPUT.open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=COLUMNS);w.writeheader();w.writerows(rows)
    print(f'wrote {len(rows)} rows to {OUTPUT}')

if __name__=='__main__': main()
