import httpx,re
from app.models import Tender
from app.connectors.common import soup_text,excerpt
URL='https://evo.isepvo.sk/evoportal/sk-sk/Public/OrderSearch/Index'
async def fetch(countries,start,min_eur):
 async with httpx.AsyncClient(timeout=40,follow_redirects=True,headers={'User-Agent':'Mozilla/5.0 GOODRAM-Tender-Intelligence/1.4.2'}) as c:
  r=await c.get(URL);r.raise_for_status();s,text=soup_text(r.text);ids=set(re.findall(r'(?:Detail\?id=|/detail/)(\d+)',r.text,re.I));stats={'status':r.status_code,'bytes':len(r.content),'ids':len(ids),'html_excerpt':excerpt(text,1500),'relevant':0}
  if not ids:raise RuntimeError('Slovakia discovery found 0 ids; '+str(stats))
 return [],stats
