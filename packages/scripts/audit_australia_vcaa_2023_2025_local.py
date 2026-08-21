from __future__ import annotations

import csv
import subprocess
from pathlib import Path

ROOT=Path('/home/ubuntu/ga-em-dm-resource-hub')
PDF_DIR=ROOT/'research/australia_vcaa_2023_2025'
OUT=ROOT/'research/australia_vcaa_2023_2025_local_audit.csv'
PAGE='https://www.vcaa.vic.edu.au/assessment/vce/examination-specifications-past-examinations-and-examination-reports/general-mathematics'
ITEMS=[
 ('2025_general_maths_exam_1.pdf','2025 VCE General Mathematics examination 1','https://www.vcaa.vic.edu.au/sites/default/files/2025-11/2025-GeneralMaths1_0.pdf','exam'),
 ('2025_general_maths_exam_2.pdf','2025 VCE General Mathematics examination 2','https://www.vcaa.vic.edu.au/sites/default/files/2025-11/2025-GeneralMaths2.pdf','exam'),
 ('2024_general_maths_exam_1.pdf','2024 VCE General Mathematics examination 1','https://www.vcaa.vic.edu.au/sites/default/files/Documents/exams/mathematics/2024/2024GeneralMaths1-w.pdf','exam'),
 ('2024_general_maths_exam_2.pdf','2024 VCE General Mathematics examination 2','https://www.vcaa.vic.edu.au/sites/default/files/Documents/exams/mathematics/2024/2024GeneralMaths2-w.pdf','exam'),
 ('2024_general_maths_exam_1_marking_guidelines.pdf','2024 VCE General Mathematics exam 1 marking guidelines and sample responses','https://www.vcaa.vic.edu.au/sites/default/files/Documents/exams/mathematics/2024/2024genmaths1-markguideresponses.pdf','solution'),
 ('2023_general_maths_exam_1.pdf','2023 VCE General Mathematics examination 1','https://www.vcaa.vic.edu.au/sites/default/files/Documents/exams/mathematics/2023/2023genmath1-w.pdf','exam'),
 ('2023_general_maths_exam_2.pdf','2023 VCE General Mathematics examination 2','https://www.vcaa.vic.edu.au/sites/default/files/Documents/exams/mathematics/2023/2023genmath2-w.pdf','exam'),
]
FIELDS=['key','title','resource_url','page_url','file','bytes','pdf_text_chars','english_cues','substantive_cues','parser_warning','decision','reason']

def extract(path:Path)->tuple[str,str]:
    proc=subprocess.run(['pdftotext','-layout',str(path),'-'],capture_output=True,text=True)
    return proc.stdout,proc.stderr.strip()

def main()->None:
    rows=[]
    for filename,title,url,kind in ITEMS:
        path=PDF_DIR/filename
        text,warning=extract(path)
        lower=text.lower()
        english=sum(term in lower for term in ['question','answer','marks','mathematics','calculate','show that','use the graph','response'])
        substantive=sum(term in lower for term in ['question','marks','calculate','find','determine','solve','answer','response','working'])
        decision='keep' if path.exists() and path.stat().st_size>10000 and len(text)>500 and english>=3 and substantive>=3 else 'exclude'
        reason='Public VCAA PDF has substantial extracted English examination or marking-guideline content.' if decision=='keep' else 'Insufficient local evidence under the clean-content threshold.'
        rows.append({'key':filename,'title':title,'resource_url':url,'page_url':PAGE,'file':str(path),'bytes':path.stat().st_size if path.exists() else 0,'pdf_text_chars':len(text),'english_cues':english,'substantive_cues':substantive,'parser_warning':warning,'decision':decision,'reason':reason})
    with OUT.open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    for row in rows: print(row['decision'],row['key'],row['bytes'],row['pdf_text_chars'],row['english_cues'],row['substantive_cues'],row['parser_warning'])
    print(f'Wrote {len(rows)} audit rows to {OUT}')

if __name__=='__main__': main()
