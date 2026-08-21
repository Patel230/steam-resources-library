"""Targeted clean-content audit for the eligible Mahidol MUIC mathematics sample."""
from __future__ import annotations

from audit_clean_content import RESEARCH_DIR, audit_pdf, read_active_rows, write_csv

TARGET_URLS = {
    "https://muic-www-assets.muic.io/example_of_mathematics_9b6942cb44.pdf",
}
OUTPUT = RESEARCH_DIR / "clean_content_pdf_audit_thailand_mahidol_20260816.csv"


def main() -> None:
    rows = [row for row in read_active_rows() if row.get("resource_url") in TARGET_URLS]
    missing = TARGET_URLS - {row.get("resource_url", "") for row in rows}
    if missing:
        raise SystemExit(f"Expected live rows missing for: {sorted(missing)}")
    audited = [audit_pdf(row, timeout=90) for row in rows]
    fields = list(audited[0].keys())
    write_csv(OUTPUT, audited, fields)
    outcomes = {row["resource_url"]: row["decision"] for row in audited}
    print({"report": str(OUTPUT), "outcomes": outcomes})
    if any(row["decision"] != "keep" for row in audited):
        raise SystemExit("Mahidol targeted audit did not produce keep evidence")


if __name__ == "__main__":
    main()
