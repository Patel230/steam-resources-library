from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.waeconline.org.ng/e-learning/Mathematics/"
INDEX_URL = urljoin(BASE, "mathsmain.html")
OUT = Path("client/src/data/nigeria_waec_verified_resources.csv")
AUDIT = Path("research/clean_content_pdf_audit_nigeria_waec.csv")
LEDGER = Path("research/nigeria_waec_tranche_audit.csv")
TODAY = "2026-08-16"
HEADERS = {"User-Agent": "SignalAtlasResearch/1.0 (public archive verification)"}
FIELDS = [
    "country", "track", "topic_tags", "priority", "source_type", "source_title",
    "source_url", "resource_title", "resource_url", "resource_class", "language",
    "notes", "access_model", "verification_status", "free_resource",
]


def fetch(url: str) -> tuple[str, int]:
    response = requests.get(url, headers=HEADERS, timeout=(5, 12))
    response.raise_for_status()
    return response.text, response.status_code


def clean_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def title_of(soup: BeautifulSoup, fallback: str) -> str:
    title = soup.title.get_text(" ", strip=True) if soup.title else fallback
    return re.sub(r"\s+", " ", title).strip()


def inspect_page(job: tuple[str, str]) -> dict[str, str]:
    resource_url, paper_title = job
    try:
        html, status = fetch(resource_url)
    except Exception as exc:
        return {"resource_url": resource_url, "decision": "exclude", "http_status": "error", "text_chars": "0", "keywords": "", "paper_title": paper_title, "resource_title": resource_url.rsplit("/", 1)[-1], "error": str(exc)}
    soup = BeautifulSoup(html, "html.parser")
    text = clean_text(soup)
    resource_title = title_of(soup, resource_url.rsplit("/", 1)[-1])
    lower = text.lower()
    keywords = [k for k in ("question", "candidate", "performance", "weakness", "strength", "observation", "remedy") if k in lower]
    keep = len(text) >= 350 and bool(set(keywords) & {"question", "candidate", "performance", "weakness", "strength", "observation"})
    return {"resource_url": resource_url, "decision": "keep" if keep else "exclude", "http_status": str(status), "text_chars": str(len(text)), "keywords": ";".join(keywords), "paper_title": paper_title, "resource_title": resource_title, "error": ""}


def main() -> None:
    index_html, _ = fetch(INDEX_URL)
    index_soup = BeautifulSoup(index_html, "html.parser")
    paper_links: list[str] = []
    for anchor in index_soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if re.fullmatch(r"maths\d+(?:mc|nc|[A-Z]c)\.html", href, flags=re.I):
            url = urljoin(BASE, href)
            if url not in paper_links:
                paper_links.append(url)

    candidate_jobs: dict[str, str] = {}
    for paper_url in paper_links:
        try:
            paper_html, _ = fetch(paper_url)
        except Exception as exc:
            print(f"SKIP_PAPER\t{paper_url}\t{exc}")
            continue
        paper_soup = BeautifulSoup(paper_html, "html.parser")
        paper_title = title_of(paper_soup, paper_url.rsplit("/", 1)[-1])
        prefix = paper_url.rsplit("/", 1)[-1][:-6]
        for anchor in paper_soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if re.fullmatch(prefix + r"[a-z0-9]+\.html", href, flags=re.I):
                resource_url = urljoin(BASE, href)
                if resource_url != paper_url:
                    candidate_jobs.setdefault(resource_url, paper_title)

    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(inspect_page, item) for item in candidate_jobs.items()]
        results = [future.result() for future in as_completed(futures)]

    records: list[dict[str, str]] = []
    audits: list[dict[str, str]] = []
    for result in results:
        audits.append({key: result.get(key, "") for key in ("resource_url", "decision", "http_status", "text_chars", "keywords", "paper_title")})
        if result["decision"] != "keep":
            continue
        is_question = bool(re.search(r"mq\d+\.html$", result["resource_url"], re.I))
        records.append({
            "country": "Nigeria", "track": "GA" if is_question else "EM",
            "topic_tags": "mathematics;WASSCE;question;exam analysis", "priority": "A",
            "source_type": "Official examination council e-learning archive",
            "source_title": "West African Examinations Council Mathematics e-Learning (Nigeria)",
            "source_url": INDEX_URL, "resource_title": result["resource_title"],
            "resource_url": result["resource_url"],
            "resource_class": "Question page" if is_question else "Examiner analysis",
            "language": "English",
            "notes": "Official public WAEC Nigeria e-learning page with substantive mathematics question content or examiner analysis; retained as a free web resource after direct HTTP and text-content audit.",
            "access_model": "Free public web resource",
            "verification_status": f"Official source HTTP {result['http_status']} + substantive English page audit · verified {TODAY}",
            "free_resource": "Yes",
        })

    records.sort(key=lambda row: row["resource_url"])
    audits.sort(key=lambda row: row["resource_url"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS); writer.writeheader(); writer.writerows(records)
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["resource_url", "decision", "http_status", "text_chars", "keywords", "paper_title"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames); writer.writeheader(); writer.writerows(audits)
    with LEDGER.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["paper_url", "paper_title"]); writer.writeheader()
        for paper_url in paper_links:
            writer.writerow({"paper_url": paper_url, "paper_title": paper_url.rsplit("/", 1)[-1]})
    print(f"papers={len(paper_links)} candidates={len(candidate_jobs)} records={len(records)} audits={len(audits)}")


if __name__ == "__main__":
    main()
