from pathlib import Path
import json
import requests

OUT = Path('/home/ubuntu/research_tmp/malaysia_peninsula_candidates')
OUT.mkdir(parents=True, exist_ok=True)
ids = ['034e0e9d-dd63-499d-b55f-7bb59d66d3c0', '43590d2f-9ffc-4dbb-8c3c-bb0def35d1aa']
base = 'https://digitallibrary.peninsulacollege.edu.my'
headers = {'User-Agent': 'SignalAtlas-research/1.0'}
rows = []
for uuid in ids:
    row = {'uuid': uuid}
    api = f'{base}/server/api/core/bitstreams/{uuid}'
    try:
        r = requests.get(api, headers=headers, timeout=(8, 20))
        row.update({'api_status': r.status_code, 'api_type': r.headers.get('content-type')})
        if r.ok and 'json' in (r.headers.get('content-type') or ''):
            meta = r.json()
            row['name'] = meta.get('name')
            row['sizeBytes'] = meta.get('sizeBytes')
            row['content'] = meta.get('_links', {}).get('content', {}).get('href')
            row['canDownload'] = meta.get('_links', {}).get('bundle', {}).get('href') is not None
            content_url = row.get('content')
            if content_url:
                c = requests.get(content_url, headers=headers, timeout=(8, 25))
                row.update({'content_status': c.status_code, 'content_type': c.headers.get('content-type'), 'content_bytes': len(c.content)})
                if c.status_code == 200 and c.content.startswith(b'%PDF'):
                    target = OUT / f'{uuid}.pdf'
                    target.write_bytes(c.content)
                    row['saved'] = str(target)
    except Exception as exc:
        row['error'] = repr(exc)
    rows.append(row)
(OUT / 'api_manifest.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(json.dumps(rows, indent=2))
