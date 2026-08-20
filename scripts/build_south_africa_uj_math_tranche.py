from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path
import requests

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'client/src/data'
RESEARCH = ROOT / 'research'
OUTPUT = DATA / 'south_africa_uj_math_verified_resources.csv'
AUDIT = RESEARCH / 'south_africa_uj_math_local_audit.csv'
CLEAN = RESEARCH / 'clean_content_pdf_audit_south_africa_uj_math.csv'
VERIFY_DATE = '2026-08-16'
FIELDS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
CANDIDATES = [
    ('University of Johannesburg — Discrete Mathematics MAT02A3, 2024 Paper C', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/Discrete-Mathematics/9954807507691', 'https://ujcontent.uj.ac.za/view/pdfCoverPage?instCode=27UOJ_INST&filePid=1313548670007691&download=true'),
    ('University of Johannesburg — Mathematics 2A MAT2WA2, 2024 Paper B', 'https://ujcontent.uj.ac.za/esploro/outputs/questionbank/Mathematics-2A/9954806907691', 'https://ujcontent.uj.ac.za/view/pdfCoverPage?instCode=27UOJ_INST&filePid=1313548370007691&download=true'),
]
ENGLISH = re.compile(r'\b(the|and|of|to|in|for|with|let|given|find|show|prove|question|problem|solution|exercise|answer|matrix|function|relation|graph|derivative|integral)\b', re.I)
QUESTIONS = re.compile(r'\b(question|problem|exercise|prove|show|find|calculate|determine|solve|let|given|derivative|integral|matrix|function)\b', re.I)

def existing_urls():
    urls=set()
    for path in DATA.glob('*_verified_resources.csv'):
        with path.open(newline='',encoding='utf-8') as fh:
            urls.update(r.get('resource_url','').strip() for r in csv.DictReader(fh) if r.get('resource_url'))
    return urls

def main():
    existing=existing_urls(); audits=[]; records=[]; clean=[]
    with tempfile.TemporaryDirectory(prefix='uj-math-') as td:
        for i,(source_title,source_url,url) in enumerate(CANDIDATES):
            pdf=Path(td)/f'{i}.pdf'; textfile=Path(td)/f'{i}.txt'
            try:
                r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=60)
                pdf.write_bytes(r.content); status=r.status_code; ctype=r.headers.get('content-type','').lower()
            except Exception as exc:
                status=0; ctype=f'error:{type(exc).__name__}'
            text=''
            if pdf.exists() and pdf.read_bytes()[:4] == b'%PDF':
                p=subprocess.run(['pdftotext','-layout',str(pdf),str(textfile)],capture_output=True,text=True,timeout=40)
                if p.returncode==0 and textfile.exists(): text=textfile.read_text(encoding='utf-8',errors='replace')
            chars=len(re.sub(r'\s+','',text)); english=len(ENGLISH.findall(text)); questions=len(QUESTIONS.findall(text)); duplicate=url in existing
            keep=status==200 and pdf.exists() and pdf.read_bytes()[:4]==b'%PDF' and chars>=500 and english>=20 and questions>=5 and not duplicate
            reason='keep' if keep else ('duplicate of existing catalog URL' if duplicate else 'not substantive English PDF')
            row={'source_title':source_title,'resource_url':url,'http_status':str(status),'content_type':ctype,'text_chars':str(chars),'english_cues':str(english),'question_cues':str(questions),'included':'Yes' if keep else 'No','reason':reason}
            audits.append(row)
            if keep:
                records.append({'country':'South Africa','track':'EM/DM','topic_tags':'mathematics;discrete mathematics;calculus;linear algebra;university exam questions','priority':'A','source_type':'First-party university repository','source_title':source_title,'source_url':source_url,'resource_title':source_title,'resource_url':url,'resource_class':'University past examination paper','language':'English','notes':'Open-access University of Johannesburg repository PDF; direct file access, local text extraction, substantive question evidence, and duplicate checks passed.','access_model':'Free public PDF','verification_status':f'HTTP 200 · verified {VERIFY_DATE}','free_resource':'Yes'})
                clean.append({**row,'decision':'keep','evidence':f'text_chars={chars}; english_cues={english}; question_cues={questions}'})
    with AUDIT.open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=list(audits[0].keys())); w.writeheader(); w.writerows(audits)
    with OUTPUT.open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=FIELDS); w.writeheader(); w.writerows(records)
    with CLEAN.open('w',newline='',encoding='utf-8') as fh:
        fields=list(clean[0].keys()) if clean else ['source_title','resource_url','decision','evidence']; w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(clean)
    print({'candidates':len(CANDIDATES),'kept_new':len(records),'audit':str(AUDIT.relative_to(ROOT)),'clean':str(CLEAN.relative_to(ROOT))})
    for r in audits: print(r)

if __name__ == '__main__': main()
