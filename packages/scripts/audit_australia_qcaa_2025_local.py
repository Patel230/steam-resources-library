from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
PDF_DIR = ROOT / 'research/australia_state_audit/qcaa_general'
OUT = ROOT / 'research/australia_qcaa_2025_local_audit.csv'
COLS = ['key', 'title', 'page_url', 'resource_url', 'local_path', 'http_status', 'content_type', 'file_bytes', 'pdf_text_chars', 'english_cues', 'substantive_cues', 'parser_warning', 'decision', 'reason']
CANDIDATES = [
    {
        'key': 'qcaa-2025-general-mathematics-paper-1-multiple-choice',
        'title': 'QCAA External assessment 2025 General Mathematics Paper 1 multiple-choice question book',
        'page_url': 'https://www.qcaa.qld.edu.au/senior/senior-subjects/syllabuses/mathematics/general-mathematics',
        'resource_url': 'https://www.qcaa.qld.edu.au/downloads/senior-qce/mathematics/snr_maths_general_25_ea_p1_mc_question.pdf',
        'filename': 'snr_maths_general_25_ea_p1_mc_question.pdf',
    },
]

def extract(path: Path) -> tuple[str, str]:
    proc = subprocess.run(['pdftotext', str(path), '-'], capture_output=True, text=True)
    warning = proc.stderr.strip().replace('\n', ' | ')
    return proc.stdout, warning

def main() -> None:
    rows = []
    for item in CANDIDATES:
        path = PDF_DIR / item['filename']
        text, warning = extract(path)
        lower = text.lower()
        english = sum(bool(re.search(pattern, lower)) for pattern in [r'external assessment', r'general mathematics', r'question', r'answer', r'which', r'option', r'calculate', r'probability', r'graph'])
        substantive = sum(bool(re.search(pattern, lower)) for pattern in [r'question\s+\d+', r'which', r'option', r'what is', r'calculate', r'probability', r'graph', r'equation'])
        decision = 'keep' if len(text) >= 1000 and english >= 3 and substantive >= 3 else 'exclude'
        reason = 'Substantive English external-assessment question book with multiple item-level question cues.' if decision == 'keep' else 'Insufficient extracted substantive English evidence.'
        rows.append({
            'key': item['key'], 'title': item['title'], 'page_url': item['page_url'], 'resource_url': item['resource_url'],
            'local_path': str(path), 'http_status': '200 browser-verified', 'content_type': 'application/pdf',
            'file_bytes': path.stat().st_size, 'pdf_text_chars': len(text), 'english_cues': english,
            'substantive_cues': substantive, 'parser_warning': warning or 'none', 'decision': decision, 'reason': reason,
        })
    with OUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {OUT}')
    for row in rows:
        print(row['key'], row['decision'], row['pdf_text_chars'], row['english_cues'], row['substantive_cues'])

if __name__ == '__main__':
    main()
