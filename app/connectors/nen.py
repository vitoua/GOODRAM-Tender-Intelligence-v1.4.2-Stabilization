import asyncio,httpx,re
from datetime import datetime
from urllib.parse import urljoin
from app.models import Tender
from app.filters import relevant
from app.connectors.common import soup_text,find_after,date_any,cpvs,clean
BASE='https://nen.nipez.cz';MAX_DETAILS=100
async def fetch(countries,start,min_eur):
 stats={'pages':0,'ids':0,'details_ok':0,'timeouts':0,'active':0,'relevant':0};links={}
 async with httpx.AsyncClient(timeout=30,follow_redirects=True,headers={'User-Agent':'GOODRAM-Tender-Intelligence/1.4.2'}) as c:
  for page in range(1,5):
   u=BASE+'/verejne-zakazky'+('' if page==1 else f'/p:vz:page={page}');r=await c.get(u);r.raise_for_status();stats['pages']+=1;s,_=soup_text(r.text)
   for a in s.select('a[href*="/detail-zakazky/"]'):
    m=re.search(r'/detail-zakazky/([^?#]+)',a.get('href',''))
    if m:links[m.group(1)]=urljoin(BASE,a['href'])
  stats['ids']=len(links);sem=asyncio.Semaphore(15)
  async def load(item):
   nid,u=item
   async with sem:
    try:r=await c.get(u,timeout=25);r.raise_for_status();return nid,u,r.text
    except Exception:return None
  docs=await asyncio.gather(*(load(x) for x in list(links.items())[:MAX_DETAILS]));out=[]
  for row in filter(None,docs):
   nid,u,html=row;stats['details_ok']+=1;s,text=soup_text(html);title=find_after(text,'Název zadávacího postupu',['Zadavatel','Systémové číslo NEN']) or clean(s.title.get_text());buyer=find_after(text,'Zadavatel',['Systémové číslo NEN','Aktuální stav']);pub=date_any(find_after(text,'Datum uveřejnění ZP na profil',['Specifikace podání','Kontaktní osoba']));ddl=date_any(find_after(text,'Lhůta pro podání nabídek',['Kontaktní osoba','Předmět']));status=find_after(text,'Aktuální stav ZP',['Rozdělení na části','Evidenční číslo'])
   if pub and pub<start or not ddl or ddl<datetime.now() or any(x in status.casefold() for x in ('zrušen','zadán','ukončen')):continue
   stats['active']+=1;codes=cpvs(text);desc=find_after(text,'Popis předmětu',['Kód z číselníku','Hlavní místo plnění'])
   if not relevant('nen',codes,title+' '+desc):continue
   stats['relevant']+=1;out.append(Tender(nid,'nen','CZE',title,buyer,deadline=ddl,published=pub,url=u,description=desc,procurement_id=nid,cpv=codes,source_links={'NEN':u}))
 return out,stats
