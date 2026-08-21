from __future__ import annotations

import csv
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urljoin

import requests

BASE = "https://gear.kku.ac.th/~polpinit/classes/188200_2010_1/"
CANDIDATES = [
    ("Homework 1", "HW/HW1.pdf", "Assignments"),
    ("Homework 2", "HW/HW2.pdf", "Assignments"),
    ("Homework 3", "HW/HW3.pdf", "Assignments"),
    ("Homework 4", "HW/HW4.pdf", "Assignments"),
    ("Homework 5", "HW/HW5.pdf", "Assignments"),
    ("Homework 5 Solution", "HW/HW5_Solution.pdf", "Solutions"),
    ("Homework 6", "HW/HW6.pdf", "Assignments"),
    ("Homework 6 Solution", "HW/HW6_Solution.pdf", "Solutions"),
    ("Midterm 2010", "midterm_2010_1.pdf", "Exams"),
    ("Quiz 1 2009 Summer", "Quiz1_2009_summer.pdf", "Quizzes"),
    ("Quiz 1 2009", "Quiz1_2009_1.pdf", "Quizzes"),
    ("Quiz 2 2009 Summer", "Quiz2_2009_summer.pdf", "Quizzes"),
]


def extract_text(data: bytes) -> str:
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "candidate.pdf"
        txt = Path(td) / "candidate.txt"
        pdf.write_bytes(data)
        proc = subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], capture_output=True, text=True, timeout=20)
        if proc.returncode != 0 or not txt.exists():
            return ""
        return txt.read_text(encoding="utf-8", errors="ignore")


def main() -> None:
    out = Path("research/thailand_kku_188200_followup_audit.csv")
    rows = []
    for title, rel, resource_class in CANDIDATES:
        url = urljoin(BASE, rel)
        row = {"title": title, "url": url, "resource_class": resource_class}
        try:
            response = requests.get(url, timeout=(5, 8), headers={"User-Agent": "SignalAtlasResearch/1.0"})
            data = response.content
            text = extract_text(data) if response.status_code == 200 and data.startswith(b"%PDF") else ""
            ascii_words = re.findall(r"\b[A-Za-z]{3,}\b", text)
            question_markers = len(re.findall(r"(?im)\b(question|prove|show that|determine|calculate|find|solve|evaluate|let|given)\b", text))
            row.update({
                "status": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "bytes": len(data),
                "pdf_signature": data.startswith(b"%PDF"),
                "pages_or_text": len(text.splitlines()),
                "english_word_count": len(ascii_words),
                "question_markers": question_markers,
                "text_sample": " ".join(text.split())[:240],
            })
        except Exception as exc:
            row.update({"status": "ERROR", "content_type": "", "bytes": 0, "pdf_signature": False, "pages_or_text": 0, "english_word_count": 0, "question_markers": 0, "text_sample": str(exc)})
        rows.append(row)
        print(row, flush=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
