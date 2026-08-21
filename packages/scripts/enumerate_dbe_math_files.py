from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

session_urls = {
    '2025_nov': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2025NovemberNSCExaminationPapers.aspx',
    '2024_nov': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2024NovemberNSCExaminationPapers.aspx',
    '2023_nov': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2023NSCNovemberExamPapers.aspx',
    '2022_nov': 'https://www.education.gov.za/LinkClick.aspx?link=3294&tabid=593&portalid=0&mid=1741',
    '2021_nov': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2021NSCExamPapers.aspx',
    '2020_nov': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2020NSCExamPapers.aspx',
    '2019_nov': 'https://www.education.gov.za/LinkClick.aspx?link=2556&tabid=593&portalid=0&mid=1741',
}
headers = {'User-Agent': 'Mozilla/5.0 SignalAtlas research audit'}
for label, url in session_urls.items():
    try:
        r = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
        print(f'## {label}\t{r.status_code}\t{r.url}')
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            text = ' '.join(a.get_text(' ', strip=True).split())
            href = urljoin(r.url, a['href'])
            combined = f'{text} {href}'.lower()
            if any(k in combined for k in ('mathematics', 'mathematical literacy', 'maths')):
                print(f'{text}\t{href}')
    except Exception as exc:
        print(f'## {label}\tERROR\t{exc}')
