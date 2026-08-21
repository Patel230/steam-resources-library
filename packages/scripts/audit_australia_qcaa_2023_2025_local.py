from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
PDF_DIR = ROOT / 'research/australia_state_audit/qcaa_general'
OUT = ROOT / 'research/australia_qcaa_2023_2025_local_audit.csv'
COLS = ['key','title','page_url','resource_url','local_path','http_status','content_type','file_bytes','pdf_text_chars','english_cues','substantive_cues','parser_warning','decision','reason']
PAGE = 'https://www.qcaa.qld.edu.au/senior/senior-subjects/syllabuses/mathematics/general-mathematics'
BASE = 'https://www.qcaa.qld.edu.au/downloads/senior-qce/mathematics/'
FILES = [
 ('25_mark_guide_pub','snr_maths_general_25_ea_mark_guide_pub.pdf','2025 General Mathematics marking guide'),
 ('25_p1_question_response','snr_maths_general_25_ea_p1_question_response.pdf','2025 General Mathematics Paper 1 question and response book'),
 ('25_p2_question_response','snr_maths_general_25_ea_p2_question_response.pdf','2025 General Mathematics Paper 2 question and response book'),
 ('25_p1_mc_question','snr_maths_general_25_ea_p1_mc_question.pdf','2025 General Mathematics Paper 1 multiple-choice question book'),
 ('24_mark_guide_pub','snr_maths_general_24_ea_mark_guide_pub.pdf','2024 General Mathematics marking guide'),
 ('24_p1_mc_question','snr_maths_general_24_ea_p1_mc_question.pdf','2024 General Mathematics Paper 1 multiple-choice question book'),
 ('24_p1_question_response','snr_maths_general_24_ea_p1_question_response.pdf','2024 General Mathematics Paper 1 question and response book'),
 ('24_p2_question_response','snr_maths_general_24_ea_p2_question_response.pdf','2024 General Mathematics Paper 2 question and response book'),
 ('23_mark_guide_pub','snr_maths_general_23_ea_mark_guide_pub.pdf','2023 General Mathematics marking guide'),
 ('23_p1_mc_question','snr_maths_general_23_ea_p1_mc_question.pdf','2023 General Mathematics Paper 1 multiple-choice question book'),
 ('23_p1_question_response','snr_maths_general_23_ea_p1_question_response.pdf','2023 General Mathematics Paper 1 question and response book'),
 ('23_p2_question_response','snr_maths_general_23_ea_p2_question_response.pdf','2023 General Mathematics Paper 2 question and response book'),
]

def extract(path: Path) -> tuple[str,str]:
    proc = subprocess.run(['pdftotext', str(path), '-'], capture_output=True, text=True)
    return proc.stdout, proc.stderr.strip().replace('\n',' | ') or 'none'

def main() -> None:
    rows=[]
    for key, filename, title in FILES:
        path=PDF_DIR/filename
        if not path.exists():
            rows.append({'key':key,'title':title,'page_url':PAGE,'resource_url':BASE+filename,'local_path':str(path),'http_status':'browser download missing','content_type':'unknown','file_bytes':0,'pdf_text_chars':0,'english_cues':0,'substantive_cues':0,'parser_warning':'not downloaded','decision':'exclude','reason':'Official page exposed the candidate but browser download was not received locally.'})
            continue
        text, warning=extract(path); lower=text.lower()
        english=sum(bool(re.search(p, lower)) for p in [r'external assessment',r'general mathematics',r'question',r'response',r'marking guide',r'criterion',r'answer',r'which',r'calculate',r'probability',r'graph'])
        substantive=sum(bool(re.search(p, lower)) for p in [r'question\s+\d+',r'criterion',r'marking guide',r'mark allocation',r'assessment objectives',r'response',r'which',r'option',r'calculate',r'probability',r'graph',r'answer'])
        decision='keep' if len(text)>=1000 and english>=3 and substantive>=3 else 'exclude'
        reason='Official English question/response or marking-guide PDF with substantive item-level content.' if decision=='keep' else 'Insufficient extracted substantive English evidence.'
        rows.append({'key':key,'title':title,'page_url':PAGE,'resource_url':BASE+filename,'local_path':str(path),'http_status':'200 browser-verified','content_type':'application/pdf','file_bytes':path.stat().st_size,'pdf_text_chars':len(text),'english_cues':english,'substantive_cues':substantive,'parser_warning':warning,'decision':decision,'reason':reason})
    with OUT.open('w',newline='',encoding='utf-8') as handle:
        w=csv.DictWriter(handle,fieldnames=COLS); w.writeheader(); w.writerows(rows)
    for row in rows: print(row['key'],row['decision'],row['pdf_text_chars'],row['english_cues'],row['substantive_cues'])

if __name__=='__main__': main()
