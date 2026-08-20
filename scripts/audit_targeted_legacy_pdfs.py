"""Re-audit two legacy PDFs after transient full-catalog fetch failures.

This preserves fresh direct HTTP/extraction evidence in the same schema consumed by
the catalogue's clean-content integrity gate.
"""

from __future__ import annotations

from audit_clean_content import RESEARCH_DIR, audit_pdf, read_active_rows, write_csv


TARGET_URLS = {
    "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025Gauss7Contest.pdf",
    "https://gate2026.iitg.ac.in/doc/download/2025/XH-C1-2025.pdf",
}
OUTPUT = RESEARCH_DIR / "clean_content_pdf_audit_targeted_legacy_20260815.csv"


def main() -> None:
    rows = [row for row in read_active_rows() if row.get("resource_url") in TARGET_URLS]
    missing = TARGET_URLS - {row.get("resource_url", "") for row in rows}
    if missing:
        raise SystemExit(f"Expected live rows missing for: {sorted(missing)}")

    audited = [audit_pdf(row, timeout=60) for row in rows]
    fields = list(audited[0].keys())
    write_csv(OUTPUT, audited, fields)
    outcomes = {row["resource_url"]: row["decision"] for row in audited}
    print({"report": str(OUTPUT), "outcomes": outcomes})
    if any(row["decision"] != "keep" for row in audited):
        raise SystemExit("Targeted audit did not produce keep evidence for every live target")


if __name__ == "__main__":
    main()
