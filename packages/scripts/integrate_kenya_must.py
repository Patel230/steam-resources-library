from pathlib import Path
import csv
from datetime import date

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
OUT = ROOT / 'apps/web/src/data/kenya_must_verified_resources.csv'
LEDGER = ROOT / 'research/kenya_must_clean_content_audit.csv'
HEADER = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
TODAY = date.today().isoformat()
rows = [
    ['Kenya','EM','engineering mathematics;functions;Taylor series;differential equations;sequences;university exam questions','A','First-party university repository','Meru University of Science and Technology — SME 2250 Engineering Mathematics IV examination','https://exampapers.must.ac.ke/wp-content/uploads/2020/01/SME-2250-Engineering-Maths-IV-2.pdf','Meru University of Science and Technology — SME 2250 Engineering Mathematics IV University Examination 2016/2017','https://exampapers.must.ac.ke/wp-content/uploads/2020/01/SME-2250-Engineering-Maths-IV-2.pdf','University past examination paper','English','Public MUST examination PDF; three pages with substantive English questions on functions, Taylor series, differential equations, sequences, and related engineering mathematics; browser-verified and local text extraction passed.','Free public PDF',f'HTTP 200 · browser-verified · verified {TODAY}','Yes'],
    ['Kenya','EM','engineering mathematics;arithmetic;ratios;standard form;algebra;calculus;university exam questions','A','First-party university repository','Meru University of Science and Technology — SME 2100 Engineering Mathematics I examination','https://exampapers.must.ac.ke/wp-content/uploads/2025/09/SME-2100-ENGINEERING-MATHEMATICS-I.pdf','Meru University of Science and Technology — SME 2100 Engineering Mathematics I University Examination 2024/2025','https://exampapers.must.ac.ke/wp-content/uploads/2025/09/SME-2100-ENGINEERING-MATHEMATICS-I.pdf','University past examination paper','English','Public MUST examination PDF; three pages with substantive English questions on arithmetic, ratios, standard form, algebra, and engineering mathematics; browser-verified and local text extraction passed.','Free public PDF',f'HTTP 200 · browser-verified · verified {TODAY}','Yes'],
]
existing = []
if OUT.exists():
    with OUT.open(newline='', encoding='utf-8') as f:
        existing = list(csv.reader(f))
    if existing and existing[0] != HEADER:
        raise SystemExit('Unexpected Kenya MUST header')
existing_urls = {r[8] for r in existing[1:] if len(r) >= 9}
new_rows = [r for r in rows if r[8] not in existing_urls]
with OUT.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(HEADER); w.writerows(new_rows)
with LEDGER.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['resource_url','http_status','content_type','language','substantive_content','duplicate_check','decision','evidence_path'])
    for r in new_rows:
        w.writerow([r[8],'200','application/pdf','English','keep: substantive multi-question engineering mathematics examination','non-duplicate against live Kenya chunks','keep','/home/ubuntu/ga-em-dm-resource-audit/kenya_must/manifest.json and extracted text files'])
print(f'new_rows={len(new_rows)} output={OUT}')
