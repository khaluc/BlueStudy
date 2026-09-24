"""Vendor OFL fonts from Google Fonts so the app doesn't need external font requests."""
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse
import httpx

if __name__ == '__main__':
    root=Path('apps/web/fonts');root.mkdir(parents=True,exist_ok=True)
    url='https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Be+Vietnam+Pro:wght@400;500;600&display=swap'
    with httpx.Client(timeout=30,follow_redirects=True,headers={'User-Agent':'Mozilla/5.0 Chrome/130.0.0.0 Safari/537.36'}) as client:
        response=client.get(url);response.raise_for_status();css=response.text
        links=set(re.findall(r'url\((https://[^)]+)\)',css))
        for link in sorted(links):
            assert urlparse(link).hostname=='fonts.gstatic.com'
            response=client.get(link);response.raise_for_status()
            suffix='.woff2' if response.content[:4] == b'wOF2' else '.ttf'
            name=hashlib.sha256(link.encode()).hexdigest()[:16]+suffix
            (root/name).write_bytes(response.content)
            css=css.replace(link,'/app/fonts/'+name)
        for family in ('lora','bevietnampro'):
            response=client.get('https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/OFL.txt')
            response.raise_for_status();(root/(family+'-OFL.txt')).write_text(response.text,encoding='utf-8')
        (root/'fonts.css').write_text(css,encoding='utf-8')
        print('Vendored',len(links),'font files and both OFL licenses')
