#!/usr/bin/env python3
from __future__ import annotations
import html, json, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

FOLDERS={
 '2018':'1mqApdvv7ddBc-AuX28pU2k3YEwkASJSr',
 '2017':'0B2iBVGxYHrgDVXhKTzgxUU9VNEk',
 '2016':'0B2iBVGxYHrgDbnVrQVBiZUdVUVE',
 '2015':'0B2iBVGxYHrgDflBCRWRUREEyZG9teUhlM3VGQndvcEpQal84UW5hem9KT2xyRGpRelV1NGs',
}
out=[]
for year,fid in FOLDERS.items():
    url=f'https://drive.google.com/drive/folders/{fid}'
    r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=35)
    text=html.unescape(r.text)
    names=sorted(set(re.findall(r'[^\"<>]{0,80}(?:Maths|Math|mathematics|Olympiad|Challenge)[^\"<>]{0,120}\.pdf',text,re.I)))
    # Drive embeds file metadata in escaped JSON; collect nearby pdf names and IDs.
    ids=[]
    for m in re.finditer(r'([A-Za-z0-9_-]{20,})',text):
        s=text[max(0,m.start()-300):m.end()+300]
        if re.search(r'\.pdf|Olympiad|Challenge|Math',s,re.I): ids.append(m.group(1))
    out.append({'year':year,'folder_id':fid,'status':r.status_code,'names':names,'candidate_ids':sorted(set(ids))[:100]})
Path('research/uct_drive_archive_inventory.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for x in out:
    print(x['year'],x['status'],len(x['names']),x['names'])
    print('ids',x['candidate_ids'][:20])
