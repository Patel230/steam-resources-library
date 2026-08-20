"""Create targeted direct clean-content evidence for the KKU 2009 PDF tranche.

The full requests-based audit can intermittently receive TLS EOF failures from the
legacy KKU host. This targeted verifier uses curl, which is also the documented
item-level public-access verifier for the tranche, then applies the same English,
question, and solution evidence thresholds as ``audit_clean_content.py``.
"""

from __future__ import annotations

import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from audit_clean_content import (
    ENGLISH_RE,
    QUESTION_RE,
    SOLUTION_RE,
    RESEARCH_DIR,
    is_pdf,
    metadata_status,
    read_active_rows,
    write_csv,
)


TARGET_PREFIX = "https://gear.kku.ac.th/~polpinit/classes/188200/HW/"
OUTPUT = RESEARCH_DIR / "clean_content_pdf_audit_thailand_kku_2009_20260815.csv"


def audit_with_curl(row: dict[str, str]) -> dict[str, str]:
    result = dict(row)
    result.update(
        {
            "http_status": "",
            "content_type": "",
            "bytes": "",
            "english_status": "",
            "material_status": "",
            "decision": "review",
            "evidence": "",
        }
    )
    language_status, class_status, metadata_note = metadata_status(row)
    if language_status != "pass":
        result.update(english_status="fail", material_status=class_status, decision="remove", evidence=metadata_note)
        return result
    with tempfile.TemporaryDirectory(prefix="signal-atlas-kku-2009-") as temp:
        directory = Path(temp)
        pdf_path = directory / "resource.pdf"
        request = subprocess.run(
            [
                "curl", "-L", "--silent", "--show-error", "--max-time", "45", "--connect-timeout", "15",
                "-A", "SignalAtlasCleanContentAudit/1.0", "-o", str(pdf_path), "-w", "%{http_code}|%{content_type}",
                row["resource_url"],
            ],
            capture_output=True,
            text=True,
            timeout=55,
            check=False,
        )
        raw = request.stdout.strip()
        status, content_type = (raw.split("|", 1) + [""])[:2] if "|" in raw else ("0", "")
        size = pdf_path.stat().st_size if pdf_path.exists() else 0
        result.update(http_status=status, content_type=content_type, bytes=str(size))
        if request.returncode != 0 or status != "200" or ("pdf" not in content_type.casefold() and not pdf_path.read_bytes().startswith(b"%PDF")):
            result.update(decision="remove", evidence="not a direct HTTP 200 PDF via curl")
            return result
        text = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "8", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        ).stdout[:80000]
    english_hits = len(ENGLISH_RE.findall(text))
    question_hits = len(QUESTION_RE.findall(text))
    solution_hits = len(SOLUTION_RE.findall(text))
    result["english_status"] = "pass" if english_hits >= 10 else "fail"
    result["material_status"] = "pass" if (question_hits or solution_hits) and class_status == "pass" else "fail"
    result["evidence"] = (
        f"curl_direct_http=200; english_hits={english_hits}; question_hits={question_hits}; "
        f"solution_hits={solution_hits}; class_status={class_status}; extracted_chars={len(text)}"
    )
    result["decision"] = "keep" if result["english_status"] == "pass" and result["material_status"] == "pass" else "remove"
    return result


def main() -> None:
    rows = [
        row
        for row in read_active_rows()
        if is_pdf(row) and row.get("resource_url", "").startswith(TARGET_PREFIX)
    ]
    if len(rows) != 7:
        raise SystemExit(f"Expected seven live KKU 2009 PDF rows, found {len(rows)}")
    audited = [audit_with_curl(row) for row in rows]
    write_csv(OUTPUT, audited, list(audited[0].keys()))
    outcomes = Counter(row["decision"] for row in audited)
    print({"report": str(OUTPUT), "audited": len(audited), "outcomes": dict(outcomes)})
    if outcomes != Counter({"keep": 7}):
        raise SystemExit("Targeted KKU 2009 audit did not produce keep evidence for every live PDF")


if __name__ == "__main__":
    main()
