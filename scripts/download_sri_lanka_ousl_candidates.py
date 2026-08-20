from pathlib import Path
import hashlib
import json
import time
import requests

OUT = Path('/home/ubuntu/research_tmp/sri_lanka_ousl')
OUT.mkdir(parents=True, exist_ok=True)
CANDIDATES = {
    'mhz3551_final.pdf': 'http://pqp.ou.ac.lk/bitstream/94ouslpqp/11510/1/MHZ3551-FINAL.pdf',
    'mhz3531_mpz3231_final.pdf': 'http://pqp.ou.ac.lk/bitstream/94ouslpqp/11509/1/MHZ3531-MPZ3231-FINAL.pdf',
}
manifest = []
for name, url in CANDIDATES.items():
    target = OUT / name
    row = {'name': name, 'url': url, 'status': None, 'bytes': 0}
    try:
        response = requests.get(url, timeout=(8, 25), allow_redirects=True)
        row.update({'status': response.status_code, 'final_url': response.url, 'content_type': response.headers.get('content-type', '')})
        if response.status_code == 200 and response.content.startswith(b'%PDF'):
            target.write_bytes(response.content)
            row.update({'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()})
        else:
            row['error'] = 'response was not a PDF'
    except Exception as exc:
        row['error'] = f'{type(exc).__name__}: {exc}'
    manifest.append(row)
    time.sleep(0.5)
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
