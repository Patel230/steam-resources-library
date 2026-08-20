from pathlib import Path
import csv
import hashlib
import re
import subprocess
import requests

OUT = Path('/home/ubuntu/research_tmp/thailand_tmc_audit')
OUT.mkdir(parents=True, exist_ok=True)
URLS = [
    'https://www.tmcthailand.net/TMC8th/1stTMC_R1_P3.pdf',
    'https://www.tmcthailand.net/TMC8th/1stTMC_R1_P4.pdf',
    'https://www.tmcthailand.net/TMC8th/1stTMC_R1_P5.pdf',
    'https://www.tmcthailand.net/TMC8th/1stTMC_R1_P6.pdf',
    'https://www.tmcthailand.net/TMC8th/1stTMC_R1_M1.pdf',
    'https://www.tmcthailand.net/TMC8th/1stTMC_R1_M2.pdf',
    'https://www.tmcthailand.net/TMC8th/1stTMC_R1_M3.pdf',
    'https://www.tmcthailand.net/TMC8th/1stTMC_R1_M4.pdf',
    'https://www.tmcthailand.net/TMC8th/1stTMC_R1_M5.pdf',
    'https://www.tmcthailand.net/TMC3rd/download/Exam%20TMC2/2ndTMC_P3_1stRound.pdf',
    'https://www.tmcthailand.net/TMC3rd/download/Exam%20TMC2/2ndTMC_P4_1stRound.pdf',
    'https://www.tmcthailand.net/TMC3rd/download/Exam%20TMC2/2ndTMC_P5_1stRound.pdf',
]
rows = []
for i, url in enumerate(URLS, 1):
    name = f'candidate_{i:02d}.pdf'
    path = OUT / name
    row = {'url': url, 'status': '', 'content_type': '', 'bytes': 0, 'sha256': '', 'pages': '', 'english_cues': 0, 'thai_cues': 0, 'decision': 'exclude_pending'}
    try:
        r = requests.get(url, timeout=(8, 25), allow_redirects=True)
        row.update({'status': r.status_code, 'content_type': r.headers.get('content-type', ''), 'final_url': r.url})
        if r.status_code == 200 and r.content.startswith(b'%PDF'):
            path.write_bytes(r.content)
            row.update({'bytes': len(r.content), 'sha256': hashlib.sha256(r.content).hexdigest()})
            info = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, timeout=10)
            m = re.search(r'^Pages:\s+(\d+)', info.stdout, re.M)
            row['pages'] = m.group(1) if m else ''
            txt = subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True, timeout=20).stdout
            (OUT / f'{path.stem}.txt').write_text(txt, encoding='utf-8')
            row['english_cues'] = len(re.findall(r'\b(question|answer|choose|calculate|find|prove|solve|mathematics|contest|time|marks)\b', txt, re.I))
            row['thai_cues'] = len(re.findall(r'[\u0E00-\u0E7F]', txt))
            if row['english_cues'] >= 5 and row['thai_cues'] == 0:
                row['decision'] = 'keep_candidate'
            else:
                row['decision'] = 'exclude_non_english_or_no_text'
        else:
            row['decision'] = 'exclude_not_public_pdf'
    except Exception as exc:
        row['error'] = f'{type(exc).__name__}: {exc}'
        row['decision'] = 'exclude_fetch_error'
    rows.append(row)
with (OUT / 'audit.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
    writer.writeheader()
    writer.writerows(rows)
print(f'checked={len(rows)} keep_candidates={sum(r["decision"] == "keep_candidate" for r in rows)}')
for r in rows:
    print(r)
