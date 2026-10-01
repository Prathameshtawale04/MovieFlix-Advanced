import requests
from bs4 import BeautifulSoup
def extract_page(url):
 r=requests.get(url,timeout=20,headers={'User-Agent':'MovieFlix/1.0'});r.raise_for_status();s=BeautifulSoup(r.text,'html.parser');d=s.find('meta',attrs={'name':'description'});c=s.find('link',rel='canonical');return {'title':s.title.get_text(' ',strip=True) if s.title else '','description':d.get('content','').strip() if d else '','canonical':c.get('href','') if c else ''}
