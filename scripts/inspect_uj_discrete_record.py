from __future__ import annotations

import re
import requests
from urllib.parse import urljoin

URL = "https://ujcontent.uj.ac.za/esploro/outputs/questionbank/Discrete-Mathematics/9954807507691"
response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
print("status", response.status_code, "content_type", response.headers.get("content-type"), "bytes", len(response.content))
html = response.text
for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I):
    absolute = urljoin(URL, href)
    if any(token in absolute.lower() for token in ("download", "file", "bitstream", ".pdf", "9954807507691")):
        print(absolute)
print("title_candidates", re.findall(r'<title[^>]*>(.*?)</title>', html, flags=re.I | re.S)[:2])
