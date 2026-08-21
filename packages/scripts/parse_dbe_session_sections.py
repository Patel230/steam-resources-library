from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

urls = {
    '2022_nov': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2022NovemberExams.aspx',
    '2021_nov': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2021NSCExamPapers.aspx',
    '2020_nov': 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2020NSCExamPapers.aspx',
    '2019_nov': 'https://www.education.gov.za/2019NovExams.aspx',
}
headers = {'User-Agent': 'Mozilla/5.0 SignalAtlas research audit'}
for label, url in urls.items():
    r = requests.get(url, headers=headers, timeout=30)
    print(f'## {label}\t{r.status_code}\t{r.url}')
    soup = BeautifulSoup(r.text, 'html.parser')
    headings = soup.find_all(['h2','h3'])
    for h in headings:
        title = ' '.join(h.get_text(' ', strip=True).split())
        if title.lower() not in ('mathematics', 'mathematical literacy'):
            continue
        print(f'### {title}')
        node = h
        seen = 0
        while seen < 30:
            node = node.find_next()
            if node is None:
                break
            if node.name in ('h2','h3') and node is not h:
                break
            if node.name == 'a' and node.get('href'):
                text = ' '.join(node.get_text(' ', strip=True).split())
                print(f'{text}\t{urljoin(r.url, node["href"])}')
            seen += 1
