from pathlib import Path
import json
import time
import requests

OUT = Path('/home/ubuntu/ga-em-dm-resource-hub/research/zimbabwe_buse_candidates')
OUT.mkdir(parents=True, exist_ok=True)
urls = {
    'buse_mte1101_2024.pdf': 'http://escholar.buse.ac.zw/pep/files/original/9dc4b285ca1eafcac2456b492822b48a.pdf',
}
manifest = []
for name, url in urls.items():
    row = {'name': name, 'url': url}
    try:
        r = requests.get(url, timeout=(10, 30), allow_redirects=True)
        row.update({'status': r.status_code, 'content_type': r.headers.get('content-type'), 'bytes': len(r.content), 'final_url': r.url})
        if r.ok and r.content[:4] == b'%PDF':
            (OUT / name).write_bytes(r.content)
        else:
            (OUT / (name + '.response')).write_bytes(r.content)
    except Exception as exc:
        row['error'] = repr(exc)
    manifest.append(row)
    time.sleep(0.2)
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
