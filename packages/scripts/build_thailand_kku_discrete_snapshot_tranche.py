from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA_DIR = ROOT / 'apps/web/src/data'
RESEARCH_DIR = ROOT / 'research'
OUTPUT = DATA_DIR / 'thailand_kku_discrete_snapshot_verified_resources.csv'
AUDIT = RESEARCH_DIR / 'thailand_kku_discrete_snapshot_local_audit.csv'
CLEAN = RESEARCH_DIR / 'clean_content_pdf_audit_thailand_kku_discrete_snapshot.csv'
VERIFY_DATE = '2026-08-16'
FIELDS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
SNAPSHOTS = [
    ('Khon Kaen University — Discrete Mathematics and Linear Algebra (188200), 2010', 'https://gear.kku.ac.th/~polpinit/classes/188200_2010_1/', Path('/home/ubuntu/upload/gear.kku.ac.th__polpinit_classes_188200_2010_1__1786872634391.md')),
    ('Khon Kaen University — Discrete Mathematics and Linear Algebra (188200), 2012', 'https://gear.kku.ac.th/~polpinit/classes/188200_2012_1/', Path('/home/ubuntu/upload/gear.kku.ac.th__polpinit_classes_188200_2012_1__1786872628388.md')),
]
KEEP_RE = re.compile(r'(homework|hw\d|solution|midterm|final|quiz|exam|test)', re.I)
EXCLUDE_RE = re.compile(r'(syllabus|score|attend|spreadsheet|textbook|lecture|slide|handout|report|index\.xml|assessment)', re.I)
ENGLISH_RE = re.compile(r'\b(the|and|of|to|in|for|with|let|given|find|show|prove|question|problem|solution|exercise|answer|matrix|set|function|relation|graph|linear|algebra|discrete)\b', re.I)
QUESTION_RE = re.compile(r'\b(question|problem|exercise|prove|show|find|compute|determine|solve|let|calculate|matrix|set|function|relation|graph|answer)\b', re.I)

def existing_urls() -> set[str]:
    urls = set()
    for path in DATA_DIR.glob('*_verified_resources.csv'):
        try:
            with path.open(newline='', encoding='utf-8') as fh:
                urls.update(row.get('resource_url','').strip() for row in csv.DictReader(fh) if row.get('resource_url'))
        except Exception:
            pass
    return urls

def fetch(url: str, output: Path) -> tuple[int, str]:
    proc = subprocess.run(['curl','-k','-L','--silent','--show-error','--max-time','40','--connect-timeout','12','-A','Mozilla/5.0','-o',str(output),'-w','%{http_code}|%{content_type}',url], capture_output=True, text=True, timeout=55)
    raw = proc.stdout.strip()
    if '|' not in raw:
        return 0, 'unknown'
    status, content_type = raw.split('|', 1)
    return int(status) if status.isdigit() else 0, content_type.lower()

def extract_candidates() -> list[tuple[str,str,str]]:
    out, seen = [], set()
    for source_title, page_url, snapshot in SNAPSHOTS:
        html = snapshot.read_text(encoding='utf-8', errors='replace') if snapshot.exists() else ''
        # TiddlyWiki snapshots use [[label|relative.pdf]] links.
        for raw in re.findall(r'\[\[[^\]|]+\|([^\]|]+\.pdf(?:\?[^\]|]*)?)\]\]', html, flags=re.I):
            absolute = urljoin(page_url, raw.replace(' ', '%20'))
            if KEEP_RE.search(absolute) and not EXCLUDE_RE.search(absolute) and absolute not in seen:
                seen.add(absolute)
                out.append((source_title, page_url, absolute))
    return out

def main() -> None:
    existing = existing_urls()
    candidates = extract_candidates()
    audits, records, clean_rows = [], [], []
    with tempfile.TemporaryDirectory(prefix='kku-snapshot-pdfs-') as td:
        for source_title, page_url, url in candidates:
            pdf = Path(td) / (re.sub(r'\W+', '_', url)[-110:] + '.pdf')
            status, content_type = fetch(url, pdf)
            text = ''
            if status == 200 and ('pdf' in content_type or (pdf.exists() and pdf.read_bytes()[:4] == b'%PDF')):
                txt = pdf.with_suffix('.txt')
                proc = subprocess.run(['pdftotext','-layout',str(pdf),str(txt)], capture_output=True, text=True, timeout=45)
                if proc.returncode == 0 and txt.exists():
                    text = txt.read_text(encoding='utf-8', errors='replace')
            chars = len(re.sub(r'\s+', '', text))
            english = len(ENGLISH_RE.findall(text))
            questions = len(QUESTION_RE.findall(text))
            duplicate = url in existing
            keep = status == 200 and 'pdf' in content_type and chars >= 160 and english >= 12 and questions >= 3 and not duplicate
            reason = 'keep' if keep else ('duplicate of existing catalog URL' if duplicate else 'not substantive English PDF')
            audit = {'source_title':source_title,'resource_url':url,'http_status':str(status),'content_type':content_type,'text_chars':str(chars),'english_cues':str(english),'question_cues':str(questions),'included':'Yes' if keep else 'No','reason':reason}
            audits.append(audit)
            if keep:
                label = url.rsplit('/',1)[-1].split('?',1)[0].replace('_',' ')
                records.append({'country':'Thailand','track':'DM','topic_tags':'discrete mathematics;linear algebra;logic;proof;sets;relations;graphs;counting;probability','priority':'A','source_type':'First-party university course archive','source_title':source_title,'source_url':page_url,'resource_title':f'Khon Kaen University — {label}','resource_url':url,'resource_class':'University homework, quiz, examination, or solution PDF','language':'English','notes':f'Direct public PDF linked from KKU’s English Discrete Mathematics and Linear Algebra course archive; local substantive-content and duplicate checks passed. Verified {VERIFY_DATE}.','access_model':'Free public PDF','verification_status':f'HTTP 200 · verified {VERIFY_DATE}','free_resource':'Yes'})
                clean_rows.append({**audit,'decision':'keep','evidence':f'text_chars={chars}; english_cues={english}; question_cues={questions}'})
    for path, rows, fallback in [(AUDIT,audits,['source_title','resource_url']), (OUTPUT,records,FIELDS), (CLEAN,clean_rows,['source_title','resource_url','decision','evidence'])]:
        with path.open('w', newline='', encoding='utf-8') as fh:
            fields = list(rows[0].keys()) if rows else fallback
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
    print({'candidates':len(candidates),'audited':len(audits),'kept_new':len(records),'duplicates':sum(1 for row in audits if row['reason']=='duplicate of existing catalog URL'),'out_csv':str(OUTPUT.relative_to(ROOT)),'audit_csv':str(AUDIT.relative_to(ROOT)),'clean_csv':str(CLEAN.relative_to(ROOT))})
    for row in records:
        print(row['resource_title'], row['resource_url'])

if __name__ == '__main__':
    main()

