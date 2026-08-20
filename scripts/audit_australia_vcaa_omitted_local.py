from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path('/home/ubuntu/ga-em-dm-resource-hub')
DIR=ROOT/'research/australia_vcaa_2023_2025/docx'
OUT=ROOT/'research/australia_vcaa_omitted_local_audit.csv'
PAGE='https://www.vcaa.vic.edu.au/assessment/vce/examination-specifications-past-examinations-and-examination-reports/general-mathematics'
FIELDS=['file','title','resource_url','bytes','text_chars','question_cues','solution_cues','report_cues','decision','reason']
ITEMS={
 '2025_exam_1_assessment_guide.docx':('2025 VCE General Mathematics examination 1 assessment guide','https://www.vcaa.vic.edu.au/sites/default/files/2025-11/2025-GeneralMaths1-assessment-guide.docx'),
 '2025_exam_2_assessment_guide.docx':('2025 VCE General Mathematics examination 2 assessment guide','https://www.vcaa.vic.edu.au/sites/default/files/2025-11/2025-GeneralMaths2-assessment-guide.docx'),
 '2025_exam_1_report.docx':('2025 VCE General Mathematics 1 external assessment report','https://www.vcaa.vic.edu.au/sites/default/files/2026-02/2025-GeneralMaths1-report.docx'),
 '2025_exam_2_report.docx':('2025 VCE General Mathematics 2 external assessment report','https://www.vcaa.vic.edu.au/sites/default/files/2026-01/2025-GeneralMaths2-report.docx'),
 '2024_exam_2_assessment_guide.docx':('2024 VCE General Mathematics exam 2 assessment guide','https://www.vcaa.vic.edu.au/sites/default/files/2025-04/2024generalmathematics2-assessment-guide.docx'),
 '2024_exam_1_report.docx':('2024 VCE General Mathematics 1 external assessment report','https://www.vcaa.vic.edu.au/sites/default/files/2025-03/2024generalmaths1-report.docx'),
 '2024_exam_2_report.docx':('2024 VCE General Mathematics 2 external assessment report','https://www.vcaa.vic.edu.au/sites/default/files/2025-03/2024generalmaths2-report.docx'),
 '2023_exam_1_report.docx':('2023 VCE General Mathematics 1 external assessment report','https://www.vcaa.vic.edu.au/sites/default/files/2025-07/2023generalmaths1-report.docx'),
 '2023_exam_2_report.docx':('2023 VCE General Mathematics 2 external assessment report','https://www.vcaa.vic.edu.au/sites/default/files/Documents/exams/mathematics/2023/2023generalmaths2%20report.docx'),
}

def text(path:Path)->str:
    with zipfile.ZipFile(path) as z:
        xml=z.read('word/document.xml')
    root=ET.fromstring(xml)
    return ' '.join((node.text or '') for node in root.iter() if node.tag.endswith('}t'))

def main()->None:
    rows=[]
    for fn,(title,url) in ITEMS.items():
        p=DIR/fn; t=text(p) if p.exists() else ''
        low=t.lower()
        q=sum(1 for x in ['question','multiple choice','marks','item','exam'] if x in low)
        s=sum(1 for x in ['solution','response','worked','marking','acceptable answer','sample response'] if x in low)
        r=sum(1 for x in ['report','performance','students','percentage','strengths','weaknesses'] if x in low)
        # Reports and assessment guides are retained only if they publish actual answer/marking content;
        # contextual commentary alone is excluded under the clean-content policy.
        has_answer_mark_table=('guide answer mark' in low or 'question number' in low and 'worked solution' in low or 'sample response' in low)
        keep=has_answer_mark_table and ('assessment guide' in title.lower() or 'sample response' in low or 'worked' in low)
        decision='keep' if keep else 'exclude'
        reason='Visible official assessment/solution material contains substantive response or marking content.' if keep else 'Official guide/report is context or assessment commentary without independently auditable question/solution content; excluded under clean-content policy.'
        rows.append({'file':fn,'title':title,'resource_url':url,'bytes':p.stat().st_size if p.exists() else 0,'text_chars':len(t),'question_cues':q,'solution_cues':s,'report_cues':r,'decision':decision,'reason':reason})
    with OUT.open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    for row in rows: print(row['decision'],row['file'],row['bytes'],row['text_chars'],row['question_cues'],row['solution_cues'],row['report_cues'])
    print(f'Wrote {len(rows)} rows to {OUT}')

if __name__=='__main__': main()
