import csv
from pathlib import Path

ROOT = Path('/home/ubuntu/ga-em-dm-resource-hub')
DATA = ROOT / 'apps/web/src/data/australia_nesa_2016_2019_verified_resources.csv'
LOCAL = ROOT / 'research/australia_nesa_2016_2019_local_audit.csv'
OUT = ROOT / 'research/clean_content_pdf_audit_australia_nesa_2016_2019_20260816.csv'
BASE_FIELDS = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
EXTRA_FIELDS = ['_file','_line','http_status','content_type','bytes','english_status','material_status','decision','evidence']

with DATA.open(newline='', encoding='utf-8') as handle:
    resources = list(csv.DictReader(handle))
with LOCAL.open(newline='', encoding='utf-8') as handle:
    audits = {row['resource_url'].strip().lower(): row for row in csv.DictReader(handle)}

rows = []
for line, resource in enumerate(resources, start=2):
    audit = audits[resource['resource_url'].strip().lower()]
    if audit['substantive'] != 'keep':
        raise RuntimeError(f"not a keep decision: {resource['resource_url']}")
    row = {field: resource.get(field, '') for field in BASE_FIELDS}
    row.update({
        '_file': str(DATA.relative_to(ROOT)),
        '_line': line,
        'http_status': audit['status'],
        'content_type': 'application/pdf',
        'bytes': audit['bytes'],
        'english_status': 'pass',
        'material_status': 'pass',
        'decision': 'keep',
        'evidence': f"browser-backed official PDF download; local pdftotext audit; text_chars={audit['text_chars']}; english_cues={audit['english_cues']}; substantive=keep",
    })
    rows.append(row)

with OUT.open('w', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=BASE_FIELDS + EXTRA_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
print(f'wrote {len(rows)} recognized keep rows to {OUT}')
