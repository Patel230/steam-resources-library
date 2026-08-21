from __future__ import annotations

import csv
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data'
OUTPUT = DATA / 'australia_scsa_2022_2025_verified_resources.csv'
AUDIT = ROOT / 'research/australia_scsa_2022_2025_url_audit.csv'
HEADERS = {'User-Agent': 'Mozilla/5.0 SignalAtlasResearch/1.0'}
PAGES = {
    'Mathematics Methods': 'https://senior-secondary.scsa.wa.edu.au/further-resources/past-atar-course-exams/mathematics-methods-past-atar-course-exams',
    'Mathematics Specialist': 'https://senior-secondary.scsa.wa.edu.au/further-resources/past-atar-course-exams/mathematics-specialist-past-atar-course-exams',
}
COLUMNS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']


def existing_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob('*.csv'):
        if path in {OUTPUT, DATA / 'final_resources.csv'}:
            continue
        with path.open(newline='', encoding='utf-8') as handle:
            urls.update(row.get('resource_url', '').strip().lower() for row in csv.DictReader(handle) if row.get('resource_url'))
    return urls


def candidates() -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for subject, page in PAGES.items():
        response = requests.get(page, headers=HEADERS, timeout=40)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for anchor in soup.select('a[href]'):
            label = anchor.get_text(' ', strip=True)
            match = re.search(r'\b(2022|2023|2024|2025)\b', label)
            if not match:
                continue
            lower = label.lower()
            if 'formula' in lower or 'summary' in lower or 'report' in lower:
                continue
            if 'examination' not in lower and 'marking key' not in lower:
                continue
            found.append({'subject': subject, 'year': match.group(1), 'label': label, 'kind': 'solution' if 'marking key' in lower else 'exam', 'resource_url': urljoin(page, anchor['href']), 'source_url': page})
    return found


def verify(item: dict[str, str]) -> tuple[str, int, str]:
    result = subprocess.run(['curl', '-L', '-I', '--max-time', '35', '-A', HEADERS['User-Agent'], item['resource_url']], capture_output=True, text=True, check=False)
    blocks = [block for block in result.stdout.split('\r\n\r\n') if 'HTTP/' in block]
    headers = blocks[-1] if blocks else result.stdout
    status = re.search(r'HTTP/\S+\s+(\d{3})', headers)
    content = re.search(r'(?im)^content-type:\s*(.+)$', headers)
    return item['resource_url'], int(status.group(1)) if status else 0, content.group(1).strip() if content else ''


def main() -> None:
    existing = existing_urls()
    unique: dict[str, dict[str, str]] = {}
    for item in candidates():
        key = item['resource_url'].strip().lower()
        if key not in existing:
            unique[key] = item
    items = list(unique.values())
    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(verify, item) for item in items]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url.lower()] = (status, content_type)
    verified = [item for item in items if statuses[item['resource_url'].lower()][0] == 200]
    if len(verified) < 24:
        raise RuntimeError(f'Refusing to pad Australia tranche: only {len(verified)} of {len(items)} candidates returned HTTP 200')
    with OUTPUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for item in verified:
            solution = item['kind'] == 'solution'
            writer.writerow({'country':'Australia','track':'EM','topic_tags':'mathematics;calculus;functions;probability;statistics;algebra;geometry;assessment;past year questions','priority':'A','source_type':'State examination authority archive','source_title':f"SCSA {item['subject']} past ATAR course exams (official)",'source_url':item['source_url'],'resource_title':f"SCSA {item['year']} {item['subject']} — {item['label']}",'resource_url':item['resource_url'],'resource_class':'Solution archive' if solution else 'Exam paper','language':'English','notes':'Official SCSA public English assessment document; exam paper or marking key retained, while formula sheets and reports are excluded.','access_model':'Free public web resource','verification_status':'HTTP 200 · verified 2026-08-16','free_resource':'Yes'})
    with AUDIT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['resource_url','http_status','content_type','included'])
        for item in items:
            url = item['resource_url']
            writer.writerow([url, *statuses[url.lower()], 'Yes' if statuses[url.lower()][0] == 200 else 'No'])
    print(f'Candidates={len(items)} verified={len(verified)} output={OUTPUT}')


if __name__ == '__main__':
    main()
