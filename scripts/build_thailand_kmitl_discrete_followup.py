#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, re, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
URLS=[
"https://www.it.kmitl.ac.th/~pattarachai/DiscreteMath/PDF/myDiscrete_Week1.pdf",
"https://www.it.kmitl.ac.th/~pattarachai/DiscreteMath/PDF/myDiscrete_Week2.pdf",
"https://www.it.kmitl.ac.th/~pattarachai/DiscreteMath/PDF/myDiscrete_Week3.pdf",
"https://www.it.kmitl.ac.th/~pattarachai/DiscreteMath/PDF/myDiscrete_Week4.pdf",
"https://www.it.kmitl.ac.th/~pattarachai/DiscreteMath/PDF/myDiscrete_Week7.pdf",
]
AUDIT=ROOT/"research/thailand_kmitl_discrete_followup_audit.csv"
CLEAN=ROOT/"research/clean_content_pdf_audit_thailand_kmitl_discrete_followup.csv"
OUT=ROOT/"client/src/data/thailand_kmitl_discrete_followup_verified_resources.csv"
FIELDS=["country","track","topic_tags","priority","source_type","source_title","source_url","resource_title","resource_url","resource_class","language","notes","access_model","verification_status","free_resource"]
AF=["resource_url","http_status","content_type","bytes","sha256","pages","text_chars","math_cues","substantive_cues","decision","reason"]

def audit(url):
    x={k:"" for k in AF}; x['resource_url']=url
    try:
        r=requests.get(url,timeout=35,headers={'User-Agent':'Mozilla/5.0'})
        x.update(http_status=str(r.status_code),content_type=r.headers.get('content-type','').split(';')[0],bytes=str(len(r.content)),sha256=hashlib.sha256(r.content).hexdigest())
        if r.status_code!=200: x.update(decision='remove',reason='HTTP status not 200'); return x
        with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
            f.write(r.content); f.flush()
            text=subprocess.run(['pdftotext','-layout',f.name,'-'],capture_output=True,text=True,timeout=30).stdout
            info=subprocess.run(['pdfinfo',f.name],capture_output=True,text=True,timeout=30).stdout
        m=re.search(r'^Pages:\s+(\d+)',info,re.M); x['pages']=m.group(1) if m else '0'; x['text_chars']=str(len(text))
        math=[r'\blogic',r'\bproof',r'\bset',r'\brelation',r'\bfunction',r'\bsequence',r'\bseries',r'\binduction',r'\brecursion',r'\bgraph',r'\bmathemat']
        sub=[r'\bquestion',r'\bexercise',r'\bexample',r'\bsolve',r'\bprove',r'\bfind',r'\banswer',r'\b1\.',r'\b2\.',r'\btheorem']
        mc=[p for p in math if re.search(p,text,re.I)]; sc=[p for p in sub if re.search(p,text,re.I)]
        x['math_cues']=';'.join(mc); x['substantive_cues']=';'.join(sc)
        if len(text)>=500 and len(mc)>=3 and len(sc)>=2: x.update(decision='keep',reason='public English discrete-mathematics PDF with substantive examples/exercises or proof material')
        else: x.update(decision='remove',reason='insufficient English substantive discrete-mathematics evidence')
    except Exception as e: x.update(decision='remove',reason=f'verification error: {type(e).__name__}')
    return x

def main():
    existing=set()
    for p in (ROOT/'client/src/data').glob('thailand*.csv'):
        with p.open(encoding='utf-8',newline='') as f: existing.update(r.get('resource_url','').strip().lower() for r in csv.DictReader(f))
    with ThreadPoolExecutor(max_workers=5) as ex: audits=sorted(list(ex.map(audit,URLS)),key=lambda x:x['resource_url'])
    with AUDIT.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=AF); w.writeheader(); w.writerows(audits)
    rows=[]; clean=[]
    for a in audits:
        if a['decision']!='keep' or a['resource_url'].lower() in existing: continue
        stem=Path(a['resource_url']).stem.replace('_',' ')
        rows.append({'country':'Thailand','track':'DM','topic_tags':'discrete mathematics;logic;proof;sets;functions;sequences;recursion','priority':'A','source_type':'Official university course archive','source_title':'KMITL Discrete Mathematics course homepage','source_url':'https://www.it.kmitl.ac.th/~pattarachai/DiscreteMath/','resource_title':f'KMITL Discrete Mathematics — {stem}','resource_url':a['resource_url'],'resource_class':'Assignment','language':'English','notes':'Official KMITL course PDF linked from the instructor-maintained Discrete Mathematics page; retained after local substantive English DM audit.','access_model':'Free public web resource','verification_status':'Official source HTTP 200 + local substantive audit · verified 2026-08-16','free_resource':'Yes'})
        clean.append({'resource_url':a['resource_url'],'local_file':Path(a['resource_url']).name,'decision':'keep','text_chars':a['text_chars'],'english_cues':a['math_cues'],'substantive_cues':a['substantive_cues'],'reason':a['reason']})
    with OUT.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    with CLEAN.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=['resource_url','local_file','decision','text_chars','english_cues','substantive_cues','reason']); w.writeheader(); w.writerows(clean)
    print(f'candidates={len(URLS)} audited={len(audits)} keep={sum(a["decision"]=="keep" for a in audits)} new_rows={len(rows)}')
    print(AUDIT); print(OUT); print(CLEAN)
if __name__=='__main__': main()
