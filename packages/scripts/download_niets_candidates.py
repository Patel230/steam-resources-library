from pathlib import Path
import csv
import requests

BASE = "https://www.niets.or.th/en/content/download/"
FILES = {
    "math1_sample_answer_sheet.pdf": "7945",
    "math2_sample_answer_sheet.pdf": "7957",
    "common_subjects_sample_test.pdf": "7441",
    "gat_pat_form_sample_test.pdf": "7477",
    "gat_section_1_sample_answer_sheet.pdf": "8017",
    "gat_section_2_sample_answer_sheet.pdf": "8029",
    "pat1_sample_answer_sheet.pdf": "8041",
    "pat2_sample_answer_sheet.pdf": "8053",
    "pat3_sample_answer_sheet.pdf": "8065",
    "pat4_sample_answer_sheet.pdf": "8077",
    "pat5_sample_answer_sheet.pdf": "8089",
    "pat6_sample_answer_sheet.pdf": "8101",
    "pat7_1_sample_answer_sheet.pdf": "8113",
    "pat7_2_sample_answer_sheet.pdf": "8125",
    "pat7_3_sample_answer_sheet.pdf": "8137",
    "pat7_4_sample_answer_sheet.pdf": "8149",
}

root = Path(__file__).resolve().parents[1]
out = root / "research" / "niets_candidates"
out.mkdir(parents=True, exist_ok=True)
rows = []
for name, ident in FILES.items():
    url = BASE + ident
    path = out / name
    try:
        response = requests.get(url, timeout=45, allow_redirects=True)
        path.write_bytes(response.content)
        rows.append({"name": name, "id": ident, "url": url, "status": response.status_code, "content_type": response.headers.get("content-type", ""), "bytes": len(response.content), "final_url": response.url})
    except Exception as exc:
        rows.append({"name": name, "id": ident, "url": url, "status": "ERROR", "content_type": "", "bytes": 0, "final_url": str(exc)})
with (out / "download_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(f"Downloaded {len(rows)} candidate files to {out}")
