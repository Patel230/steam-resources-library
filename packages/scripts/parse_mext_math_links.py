from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

html=Path('/home/ubuntu/browser_html/studyinjapan_go_jp_examination.html_1786948294374.html').read_text(encoding='utf-8',errors='ignore')
soup=BeautifulSoup(html,'html.parser')
for a in soup.find_all('a', href=True):
    label=' '.join(a.get_text(' ',strip=True).split())
    if 'Mathematics' in label or 'mathematics' in label:
        print(f'{label}\t{urljoin("https://www.studyinjapan.go.jp/en/planning/scholarships/mext-scholarships/examination.html", a["href"])}')
