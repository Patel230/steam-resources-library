from bs4 import BeautifulSoup
from pathlib import Path
html=Path('/home/ubuntu/browser_html/lec_edu_np_old-questions_1786949144608.html').read_text(encoding='utf-8',errors='ignore')
soup=BeautifulSoup(html,'html.parser')
for a in soup.find_all('a', href=True):
    label=' '.join(a.get_text(' ',strip=True).split())
    href=a['href']
    if label in {'Engineering Math I','Sample Question BCT'} or 'Engineering' in label or href.lower().endswith(('.pdf','.pdf/')):
        print(f'{label}\t{href}')
