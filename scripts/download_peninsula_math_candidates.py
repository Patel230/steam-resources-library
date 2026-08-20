from pathlib import Path
import json
import time
import requests

OUT = Path('/home/ubuntu/research_tmp/malaysia_peninsula_candidates')
OUT.mkdir(parents=True, exist_ok=True)
items = [
    ('peninsula_dcs1123_exam_a.pdf', 'https://digitallibrary.peninsulacollege.edu.my/bitstreams/034e0e9d-dd63-499d-b55f-7bb59d66d3c0/download'),
    ('peninsula_dcs1123_exam_b.pdf', 'https://digitallibrary.peninsulacollege.edu.my/bitstreams/43590d2f-9ffc-4dbb-8c3c-bb0def35d1aa/download'),
]
manifest = []
for name, url in items:
    row = {'name': name, 'url': url}
    target = OUT / name
    try:
        r = requests.get(url, headers={'User-Agent': 'SignalAtlas-research/1.0'}, timeout=(8, 25))
        row.update({'status': r.status_code, 'content_type': r.headers.get('content-type'), 'bytes': len(r.content)})
        if r.status_code == 200 and r.content.startswith(b'%PDF'):
            target.write_bytes(r.content)
            row['saved'] = True
        else:
            row['saved'] = False
    except Exception as exc:
        row.update({'status': 'error', 'error': repr(exc), 'saved': False})
    manifest.append(row)
    time.sleep(0.5)
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
