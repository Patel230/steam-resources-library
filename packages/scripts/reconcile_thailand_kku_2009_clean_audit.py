"""Reconcile the KKU 2009 PDF tranche to its completed direct item-level audit.

The legacy KKU host intermittently closes TLS connections for concurrent requests;
the full PDF run consequently recorded transport ``review`` outcomes. The tranche
generator already completed a sequential curl verification of every direct URL,
including HTTP status, PDF content type, English cue count, and substantive cue
count. This script preserves those actual results in the standard keep-evidence
schema consumed by the catalog integrity gate. It never upgrades a failed item.
"""

from __future__ import annotations

import csv
from pathlib import Path

from audit_clean_content import RESEARCH_DIR, read_active_rows, write_csv


ROOT = Path("/home/ubuntu/ga-em-dm-resource-hub")
ITEM_AUDIT = RESEARCH_DIR / "thailand_kku_2009_homework_url_audit.csv"
OUTPUT = RESEARCH_DIR / "clean_content_pdf_audit_thailand_kku_2009_reconciled_20260815.csv"
TARGET_PREFIX = "https://gear.kku.ac.th/~polpinit/classes/188200/HW/"


def main() -> None:
    with ITEM_AUDIT.open(newline="", encoding="utf-8") as handle:
        item_by_url = {row["resource_url"]: row for row in csv.DictReader(handle)}
    live_rows = [row for row in read_active_rows() if row.get("resource_url", "").startswith(TARGET_PREFIX)]
    if len(live_rows) != 7:
        raise SystemExit(f"Expected seven live KKU 2009 PDFs, found {len(live_rows)}")
    reconciled: list[dict[str, str]] = []
    for row in live_rows:
        item = item_by_url.get(row["resource_url"])
        if item is None:
            raise SystemExit(f"Missing item-level evidence for {row['resource_url']}")
        status_ok = item.get("http_status") == "200" and "pdf" in item.get("content_type", "").casefold()
        english_hits = int(item.get("english_cues", "0"))
        substantive_hits = int(item.get("substantive_cues", "0"))
        keep = status_ok and item.get("included") == "Yes" and english_hits >= 10 and substantive_hits >= 1
        reconciled.append(
            {
                **row,
                "http_status": item.get("http_status", ""),
                "content_type": item.get("content_type", ""),
                "bytes": "",
                "english_status": "pass" if english_hits >= 10 else "fail",
                "material_status": "pass" if substantive_hits >= 1 else "fail",
                "decision": "keep" if keep else "remove",
                "evidence": (
                    "reconciled from thailand_kku_2009_homework_url_audit.csv; "
                    f"sequential_curl_http={item.get('http_status', '')}; "
                    f"english_cues={english_hits}; substantive_cues={substantive_hits}; "
                    f"item_decision={item.get('reason', '')}"
                ),
            }
        )
    write_csv(OUTPUT, reconciled, list(reconciled[0].keys()))
    failures = [row["resource_url"] for row in reconciled if row["decision"] != "keep"]
    print({"report": str(OUTPUT), "audited": len(reconciled), "keep": len(reconciled) - len(failures), "failures": failures})
    if failures:
        raise SystemExit("Not all KKU 2009 documents have completed direct keep evidence")


if __name__ == "__main__":
    main()
