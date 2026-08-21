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
OUTPUT = DATA / 'united_states_usaco_2026_verified_resources.csv'
AUDIT = ROOT / 'research/united_states_usaco_2026_url_audit.csv'
SOURCE_URL = 'https://usaco.org/index.php?page=season26contest1results'
HEADERS = {'User-Agent': 'Mozilla/5.0 SignalAtlasResearch/1.0'}
COLUMNS = ['country', 'track', 'topic_tags', 'priority', 'source_type', 'source_title', 'source_url', 'resource_title', 'resource_url', 'resource_class', 'language', 'notes', 'access_model', 'verification_status', 'free_resource']


def existing_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob('*.csv'):
        if path in {OUTPUT, DATA / 'final_resources.csv'}:
            continue
        with path.open(newline='', encoding='utf-8') as handle:
            urls.update(row.get('resource_url', '').strip().lower() for row in csv.DictReader(handle) if row.get('resource_url'))
    return urls


def candidates() -> list[dict[str, str]]:
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=40)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    anchors = list(soup.select('a[href]'))
    found: list[dict[str, str]] = []
    for index, anchor in enumerate(anchors):
        if anchor.get_text(' ', strip=True).lower() != 'view problem':
            continue
        problem_url = urljoin(SOURCE_URL, anchor['href'])
        title_element = anchor.find_previous(['strong', 'b'])
        title = title_element.get_text(' ', strip=True) if title_element else 'Official USACO problem'
        division_element = anchor.find_previous('h2')
        division = division_element.get_text(' ', strip=True).split(',')[-1].strip() if division_element else 'Contest division'
        solution_url = ''
        for next_anchor in anchors[index + 1:]:
            label = next_anchor.get_text(' ', strip=True).lower()
            if label == 'view problem':
                break
            if label == 'solution':
                solution_url = urljoin(SOURCE_URL, next_anchor['href'])
                break
        found.append({'division': division, 'title': title, 'kind': 'problem', 'resource_url': problem_url, 'source_url': SOURCE_URL})
        if solution_url:
            found.append({'division': division, 'title': title, 'kind': 'solution', 'resource_url': solution_url, 'source_url': SOURCE_URL})
    return found


def verify(item: dict[str, str]) -> tuple[str, int, str]:
    result = subprocess.run(['curl', '-L', '-I', '--max-time', '35', '-A', HEADERS['User-Agent'], item['resource_url']], capture_output=True, text=True, check=False)
    blocks = [block for block in result.stdout.split('\r\n\r\n') if 'HTTP/' in block]
    headers = blocks[-1] if blocks else result.stdout
    match = re.search(r'HTTP/\S+\s+(\d{3})', headers)
    content = re.search(r'(?im)^content-type:\s*(.+)$', headers)
    return item['resource_url'], int(match.group(1)) if match else 0, content.group(1).strip() if content else ''


def main() -> None:
    existing = existing_urls()
    raw = candidates()
    unique: dict[str, dict[str, str]] = {}
    for item in raw:
        url = item['resource_url'].strip().lower()
        if url not in existing:
            unique[url] = item
    items = list(unique.values())
    statuses: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(verify, item) for item in items]
        for future in as_completed(futures):
            url, status, content_type = future.result()
            statuses[url] = (status, content_type)
    verified = [item for item in items if statuses[item['resource_url'].lower()][0] == 200]
    if len(verified) < 20:
        raise RuntimeError(f'Refusing to pad USACO tranche: only {len(verified)} of {len(items)} candidates returned HTTP 200')
    with OUTPUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for item in verified:
            solution = item['kind'] == 'solution'
            writer.writerow({'country': 'United States', 'track': 'DM', 'topic_tags': 'discrete mathematics;algorithms;combinatorics;graph theory;programming;Olympiad;contest;problem solving', 'priority': 'A', 'source_type': 'National computing Olympiad contest archive', 'source_title': 'USA Computing Olympiad 2026 First Contest archive (official)', 'source_url': SOURCE_URL, 'resource_title': f"USACO 2026 First Contest — {item['division']} — {item['title']} ({'official solution' if solution else 'official problem'})", 'resource_url': item['resource_url'], 'resource_class': 'Solution archive' if solution else 'Olympiad problem', 'language': 'English', 'notes': 'Official USACO contest material; public problem statement or associated solution page. Login is not required to read the resource.', 'access_model': 'Free public web resource', 'verification_status': 'HTTP 200 · verified 2026-08-16', 'free_resource': 'Yes'})
    with AUDIT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['resource_url', 'http_status', 'content_type', 'included'])
        for item in items:
            url = item['resource_url']
            writer.writerow([url, *statuses[url.lower()], 'Yes' if statuses[url.lower()][0] == 200 else 'No'])
    print(f'Candidates={len(items)} verified={len(verified)} output={OUTPUT}')


if __name__ == '__main__':
    main()
