import httpx,re,json
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
BASE='https://riigihanked.riik.ee/'
VALID=re.compile(r'(?:(?:https?://[^\"\'\s<>]+)|(?:/[A-Za-z0-9_.\-/]*(?:api|rest|open-data|opendata)[A-Za-z0-9_.?=&\-/]*))',re.I)
def candidates(text,base):
 out=[]
 for m in VALID.findall(text):
  u=urljoin(base,m).rstrip('.,;:)')
  p=urlparse(u)
  if p.scheme in ('http','https') and p.netloc=='riigihanked.riik.ee' and not any(x in u for x in ('data-api','Pacific/Apia','toIsoString','bs.')):out.append(u)
 return list(dict.fromkeys(out))
async def fetch(countries,start,min_eur):
 stats={'homepage_status':0,'assets':0,'candidates':[],'json_endpoints':[]}
 async with httpx.AsyncClient(timeout=35,follow_redirects=True,headers={'User-Agent':'Mozilla/5.0 GOODRAM-Tender-Intelligence/1.4.2'}) as c:
  r=await c.get(BASE);stats['homepage_status']=r.status_code;r.raise_for_status();s=BeautifulSoup(r.text,'html.parser');cand=candidates(r.text,str(r.url));assets=[urljoin(str(r.url),x.get('src')) for x in s.select('script[src]')]
  for a in assets[:12]:
   try:x=await c.get(a);stats['assets']+=1;cand+=candidates(x.text,a)
   except:pass
  cand=list(dict.fromkeys(cand))[:30];stats['candidates']=cand
  for u in cand:
   try:x=await c.get(u);ct=(x.headers.get('content-type') or '').lower()
   except:continue
   if x.status_code==200 and ('json' in ct or x.text.lstrip().startswith(('{','['))):stats['json_endpoints'].append({'url':u,'bytes':len(x.content)})
 if not stats['json_endpoints']:raise RuntimeError('Estonia RHR beta: no public JSON feed discovered; '+json.dumps(stats,ensure_ascii=False))
 return [],stats
