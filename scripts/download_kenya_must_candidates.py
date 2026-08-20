from pathlib import Path
import json
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUT = Path('/home/ubuntu/ga-em-dm-resource-audit/kenya_must')
OUT.mkdir(parents=True, exist_ok=True)
CANDIDATES = {
    'must_sme2250_engineering_mathematics_iv_2016.pdf': 'https://exampapers.must.ac.ke/wp-content/uploads/2020/01/SME-2250-Engineering-Maths-IV-2.pdf',
    'must_sme2100_engineering_mathematics_i_2025.pdf': 'https://exampapers.must.ac.ke/wp-content/uploads/2025/09/SME-2100-ENGINEERING-MATHEMATICS-I.pdf',
}
manifest = []
for name, url in CANDIDATES.items():
    row = {'name': name, 'url': url}
    try:
        r = requests.get(url, timeout=(10, 30), headers={'User-Agent': 'Signal-Atlas-audit/1.0'}, verify=False)
        row.update({'status': r.status_code, 'content_type': r.headers.get('content-type',''), 'bytes': len(r.content), 'tls_verify': 'disabled_due_to_sandbox_chain_error; URL browser-verified'})
        if r.status_code == 200 and r.content[:4] == b'%PDF':
            path = OUT / name
            path.write_bytes(r.content)
            row['saved'] = str(path)
    except Exception as e:
        row['error'] = repr(e)
    manifest.append(row)
    time.sleep(0.5)
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
