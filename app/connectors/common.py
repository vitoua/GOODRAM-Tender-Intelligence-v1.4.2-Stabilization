import re
from datetime import datetime
from bs4 import BeautifulSoup

def clean(v):return ' '.join(str(v or '').replace('\xa0',' ').split())
def date_any(v):
 s=clean(v).replace('Z','+00:00')
 if not s:return None
 try:
  d=datetime.fromisoformat(s)
  return d.replace(tzinfo=None) if d.tzinfo else d
 except:pass
 for f in ('%Y-%m-%d','%Y-%m-%d %H:%M:%S','%d.%m.%Y %H:%M','%d/%m/%Y %H:%M','%m/%d/%Y, %I:%M %p','%Y.%m.%d. %H:%M'):
  try:return datetime.strptime(s,f)
  except:pass
 m=re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{4})[^0-9]+(\d{1,2}):(\d{2})',s)
 if m:
  try:return datetime(int(m[3]),int(m[2]),int(m[1]),int(m[4]),int(m[5]))
  except:return None
 return None
def soup_text(html):
 s=BeautifulSoup(html,'html.parser');return s,clean(s.get_text(' ',strip=True))
def find_after(text,label,stops):
 p=text.casefold().find(label.casefold())
 if p<0:return ''
 s=text[p+len(label):];ends=[s.casefold().find(x.casefold()) for x in stops];ends=[x for x in ends if x>=0]
 return clean(s[:min(ends) if ends else len(s)])
def cpvs(text):return list(dict.fromkeys(re.findall(r'\b\d{8}(?:-\d)?\b',str(text))))
def excerpt(v,n=900):return clean(v)[:n]
