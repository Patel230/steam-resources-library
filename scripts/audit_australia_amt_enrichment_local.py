import csv
import subprocess
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
PDF_DIR = ROOT / 'research/australia_amt_enrichment_pdfs'
OUT = ROOT / 'research/australia_amt_enrichment_local_audit.csv'
PAGE = 'https://amt.edu.au/department/free-activities'
ITEMS = [
 ('ramanujan-2021','2021 Maths Enrichment — Ramanujan excerpt','2021/04/2021-ENR-Ramanujan-SN-SAMPLE.pdf'),
 ('newton-2021','2021 Maths Enrichment — Newton excerpt','2021/04/2021-ENR-Newton-SN-SAMPLE.pdf'),
 ('polya-2020','2020 Maths Enrichment — Pólya excerpt','2021/04/2020-ENR-Polya-SN-SAMPLE.pdf'),
 ('noether-2020','2020 Maths Enrichment — Noether excerpt','2021/04/2020-ENR-Noether-SN-SAMPLE.pdf'),
 ('gauss-2026','2026 Maths Enrichment — Gauss excerpt','2026/2026-ENR-Gauss-SN-SAMPLE.pdf'),
 ('euler-2024','2024 Maths Enrichment — Euler excerpt','2026/2024-ENR-Euler-SN-SAMPLE.pdf'),
 ('dirichlet-2022','2022 Maths Enrichment — Dirichlet excerpt','2022/08/2022-ENR-Dirichlet-SN-SAMPLE.pdf'),
]

def main():
 rows=[]
 for key,title,rel in ITEMS:
  pdf=PDF_DIR/Path(rel).name; txt=PDF_DIR/f'{key}.txt'
  p=subprocess.run(['pdftotext','-layout',str(pdf),str(txt)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False) if pdf.exists() else None
  text=txt.read_text(errors='ignore') if txt.exists() else ''
  lower=text.lower(); cues=sum(lower.count(t) for t in ['question','problem','solution','example','find','prove','determine','calculate'])
  keep=bool(pdf.exists() and pdf.stat().st_size and len(text.strip())>=800 and cues>=4 and any(t in lower for t in ['question','problem','solution','example']))
  rows.append({'key':key,'title':title,'page_url':PAGE,'resource_url':'https://amt.edu.au/wp-content/uploads/'+rel,'filename':pdf.name,'status':200 if pdf.exists() and pdf.stat().st_size else 0,'bytes':pdf.stat().st_size if pdf.exists() else 0,'text_chars':len(text),'english_cues':cues,'extractor_warning':' '.join(p.stderr.split()) if p else 'missing file','decision':'keep' if keep else 'review','reason':'Official AMT free-activities sample contains substantive English mathematics exercises/examples.' if keep else 'Missing or below substantive threshold.'})
 with OUT.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
 print(f'wrote {len(rows)} rows to {OUT}')
 for r in rows: print(r['key'],r['status'],r['bytes'],r['text_chars'],r['english_cues'],r['decision'],r['extractor_warning'][:100])
if __name__=='__main__': main()
