from __future__ import annotations

import csv
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


"""Build only direct English practice modules visibly linked by Beaver Malaysia.

The official competition homepage links six English-language practice modules on
the ArdentEduIT static-hosting path. The generator re-reads that official page,
checks every discovered module for a direct HTTP 200 response and substantive
English question content, and excludes any duplicate catalogue URL.
"""

ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
DATA = ROOT / "apps/web/src/data"
OUTPUT = DATA / "malaysia_beaver_english_verified_resources.csv"
AUDIT = ROOT / "research/malaysia_beaver_english_url_audit.csv"
SOURCE_URL = "https://beaver.my/"
VERIFY_DATE = "2026-08-15"
USER_AGENT = "SignalAtlas/1.0 (+public-resource-audit)"


def catalog_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("*.csv"):
        if path == OUTPUT:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            urls.update(row.get("resource_url", "").strip() for row in csv.DictReader(handle))
    return urls


def fetch_text(url: str, timeout: int = 45) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def clean(text: str) -> str:
    return " ".join(text.split())


def module_name(url: str) -> str:
    decoded = unquote(urlparse(url).path)
    stem = decoded.rsplit("/", 1)[0].rsplit("/", 1)[-1]
    stem = stem.replace("BEAVER", "").replace("PRACTICE TIME", "").replace("- EN", "")
    return clean(stem.title()).replace("Pre Ecolier", "Pre-Ecolier")


def candidates(existing: set[str]) -> list[dict[str, str]]:
    soup = BeautifulSoup(fetch_text(SOURCE_URL), "html.parser")
    found: dict[str, dict[str, str]] = {}
    for anchor in soup.select("a[href]"):
        resource_url = anchor["href"].strip().replace("&amp;", "&")
        parsed = urlparse(resource_url)
        decoded_path = unquote(parsed.path)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "rawcdn.githack.com"
            or not decoded_path.lower().endswith(".html")
            or "ArdentEduIT/BeaverPracticeTime2026" not in decoded_path
            or "- EN" not in decoded_path
            or resource_url in existing
        ):
            continue
        found[resource_url] = {
            "resource_url": resource_url,
            "module": module_name(resource_url),
        }
    return sorted(found.values(), key=lambda item: item["module"])


def curl_metadata(url: str) -> tuple[int, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--silent", "--show-error", "--max-time", "45",
            "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}", url,
        ],
        capture_output=True,
        text=True,
        timeout=55,
        check=False,
    )
    raw = result.stdout.strip()
    if result.returncode != 0 or "|" not in raw:
        return 0, "unavailable"
    code, content_type = raw.split("|", 1)
    return (int(code) if code.isdigit() else 0), content_type.lower() or "unknown"


def verify(record: dict[str, str]) -> dict[str, str | int | bool]:
    status, content_type = curl_metadata(record["resource_url"])
    result: dict[str, str | int | bool] = {**record, "status": status, "content_type": content_type, "text_length": 0, "english": False}
    if status != 200 or "html" not in content_type:
        return result
    try:
        text = clean(BeautifulSoup(fetch_text(record["resource_url"]), "html.parser").get_text(" ", strip=True))
    except Exception:
        return result
    lower = text.lower()
    result["text_length"] = len(text)
    result["english"] = len(text) >= 200 and "question" in lower and ("next" in lower or "submit" in lower)
    return result


def main() -> None:
    records = candidates(catalog_urls())
    print(f"Official Beaver Malaysia non-duplicate English HTML candidates: {len(records)}")
    results: dict[str, dict[str, str | int | bool]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(verify, record) for record in records]
        for future in as_completed(futures):
            result = future.result()
            results[str(result["resource_url"])] = result

    verified = [
        results[record["resource_url"]] for record in records
        if results[record["resource_url"]]["status"] == 200
        and "html" in str(results[record["resource_url"]]["content_type"])
        and bool(results[record["resource_url"]]["english"])
    ]
    print(f"Individually verified public English Beaver modules: {len(verified)}")

    fields = [
        "country", "track", "topic_tags", "priority", "source_type", "source_title", "source_url",
        "resource_title", "resource_url", "resource_class", "language", "notes", "access_model",
        "verification_status", "free_resource",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in verified:
            module = str(result["module"])
            writer.writerow({
                "country": "Malaysia",
                "track": "DM",
                "topic_tags": "computational thinking;logic;algorithms;problem solving;interactive practice",
                "priority": "A",
                "source_type": "Official computational-thinking competition practice archive",
                "source_title": "Beaver Computational Thinking Competition Malaysia",
                "source_url": SOURCE_URL,
                "resource_title": f"Beaver Malaysia — {module} English practice questions",
                "resource_url": result["resource_url"],
                "resource_class": "Official interactive practice questions",
                "language": "English",
                "notes": "English practice module visibly linked from the official Beaver Malaysia competition homepage.",
                "access_model": "Free public interactive HTML",
                "verification_status": f"HTTP 200 · verified {VERIFY_DATE}",
                "free_resource": "Yes",
            })

    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["resource_url", "module", "http_status", "content_type", "text_length", "english_question_check", "included"])
        for record in records:
            result = results[record["resource_url"]]
            included = result in verified
            writer.writerow([
                result["resource_url"], result["module"], result["status"], result["content_type"],
                result["text_length"], result["english"], "Yes" if included else "No",
            ])
    print(f"Wrote {len(verified)} verified Beaver Malaysia records to {OUTPUT}")


if __name__ == "__main__":
    main()
