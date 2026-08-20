from pathlib import Path
import csv

root = Path('/home/ubuntu/ga-em-dm-resource-hub')
out = root / 'client/src/data/zimbabwe_buse_verified_resources.csv'
audit = root / 'research/zimbabwe_buse_clean_content_audit.csv'
header = ['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
source = 'http://escholar.buse.ac.zw/pep/items/show/2525'
pdf = 'http://escholar.buse.ac.zw/pep/files/original/9dc4b285ca1eafcac2456b492822b48a.pdf'
row = ['Zimbabwe','EM','engineering mathematics, calculus, linear algebra, probability, differential equations','A','university past exam','Bindura University of Science Education Past Exam Papers',source,'MTE1101 Engineering Mathematics 1, November 2024',pdf,'PDF question paper','English','Official BUSE Department of Statistics and Mathematics examination; 3 scanned pages; OCR verified substantive questions in probability, Gaussian elimination, limits, inequalities, functions, matrices, identities, logarithms, differentiation, differential equations, calculus, vectors, and polar curves; public no-login viewer.','Free public download','HTTP 200 · verified 2026-08-17','yes']
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='') as f:
    w = csv.writer(f); w.writerow(header); w.writerow(row)
with audit.open('w', newline='') as f:
    w = csv.writer(f); w.writerow(['country','resource_url','decision','language','question_evidence','audit_file','notes'])
    w.writerow(['Zimbabwe',pdf,'keep','English','OCR contains exam instructions and numbered substantive questions 1–5 across all three pages','research/zimbabwe_buse_candidates/buse_mte1101_2024_ocr.txt','Scanned PDF; text layer empty, but OCR reviewed page-by-page and source viewer visibly shows the examination.'])
print(out)
print(audit)
