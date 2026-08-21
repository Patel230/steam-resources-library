from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

html_path = Path('/home/ubuntu/browser_html/education_gov_za_NSCPastExaminationpapers.aspx_1786871337800.html')
soup = BeautifulSoup(html_path.read_text(errors='ignore'), 'html.parser')
base = 'https://www.education.gov.za/'
for a in soup.find_all('a'):
    text = ' '.join(a.get_text(' ', strip=True).split())
    href = a.get('href') or ''
    if any(token in text.lower() for token in ('examination', 'exam papers', 'exemplars', 'common paper')):
        print(f'{text}\t{urljoin(base, href)}')
