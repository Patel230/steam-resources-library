from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path('/home/ubuntu/browser_html/escholar_buse_ac_zw_2525_1786953549501.html')
soup = BeautifulSoup(html_path.read_text(errors='ignore'), 'html.parser')
for frame in soup.find_all('iframe'):
    src = frame.get('src', '')
    if 'pdf-embed' in src or '.pdf' in src.lower():
        print(src)
