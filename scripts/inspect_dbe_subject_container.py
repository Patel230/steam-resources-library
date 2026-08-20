from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

url = 'https://www.education.gov.za/Curriculum/NationalSeniorCertificate(NSC)Examinations/2022NovemberExams.aspx'
r = requests.get(url, headers={'User-Agent':'Mozilla/5.0 SignalAtlas audit'}, timeout=30)
soup = BeautifulSoup(r.text, 'html.parser')
h = next((x for x in soup.find_all(['h2','h3']) if 'Mathematics' == ' '.join(x.get_text(' ', strip=True).split())), None)
print('heading', bool(h))
if h:
    for parent in h.parents:
        anchors = parent.find_all('a', href=True)
        if len(anchors) >= 3:
            print('PARENT', parent.name, parent.get('class'), 'anchors', len(anchors))
            for a in anchors:
                text = ' '.join(a.get_text(' ', strip=True).split())
                print(text, urljoin(r.url, a['href']), sep='\t')
            break
