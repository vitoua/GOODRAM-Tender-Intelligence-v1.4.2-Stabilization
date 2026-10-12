import httpx,json,re
from urllib.parse import urljoin,urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from app.models import Tender
from app.filters import relevant
from app.connectors.common import date_any,clean
BASE='https://open.iub.gov.lv/data/notice'
def walk(o):
 if isinstance(o,dict):
  yield o
  for v in o.values():yield from walk(v)
 elif isinstance(o,list):
  for v in o:yield from walk(v)
def first(o,names):
 for d in walk(o):
  for k,v in d.items():
   if str(k).casefold() in {x.casefold() for x in names} and isinstance(v,(str,int,float)) and str(v).strip():return v
 return ''
def parse(raw,url):
 pid=str(first(raw,['noticeId','noticeIdentifier','id','BT-701-notice']));title=clean(first(raw,['title','noticeTitle','name','BT-21-Procedure']));buyer=clean(first(raw,['buyerName','organisationName','organizationName']));desc=clean(first(raw,['description','shortDescription','BT-24-Procedure']));pub=date_any(first(raw,['publicationDate','published','datePublished']));ddl=date_any(first(raw,['deadline','submissionDeadline','tenderDeadline','BT-131(d)-Lot']));codes=[]
 for d in walk(raw):
  for k,v in d.items():
   if 'cpv' in str(k).casefold() or 'classification' in str(k).casefold():codes+=re.findall(r'\b\d{8}\b',json.dumps(v))
 val=first(raw,['estimatedValue','totalValue','valueAmount']);cur=str(first(raw,['currency','valueCurrency']) or 'EUR')
 try:val=float(str(val).replace(',','.')) if val!='' else None
 except:val=None
 pid=pid or 'lv-'+str(abs(hash((title,buyer,url))))
 return Tender(pid,'latvia','LVA',title,buyer,val,cur,ddl,pub,url,desc,pid,list(dict.fromkeys(codes)),val if cur=='EUR' else None,source_links={'Latvia IUB':url})
async def fetch(countries,start,min_eur):
 stats={'index_requests':0,'json_files':0,'json_records':0,'parsed':0,'relevant':0,'last_url':''};out=[];q=[BASE];seen=set()
 async with httpx.AsyncClient(timeout=45,follow_redirects=True,headers={'User-Agent':'GOODRAM-Tender-Intelligence/1.4.2'}) as c:
  while q and stats['index_requests']<80 and stats['json_files']<45:
   u=q.pop(0)
   if u in seen:continue
   seen.add(u);stats['last_url']=u;r=await c.get(u);r.raise_for_status();ct=(r.headers.get('content-type') or '').lower()
   if 'json' in ct or u.endswith('.json'):
    stats['json_files']+=1;data=r.json();rows=data if isinstance(data,list) else data.get('notices') or data.get('data') or data.get('items') or [data];stats['json_records']+=len(rows)
    for raw in rows:
     if not isinstance(raw,dict):continue
     t=parse(raw,u);stats['parsed']+=1
     if t.published and t.published<start or t.deadline and t.deadline<datetime.now():continue
     if min_eur>0 and (t.value_eur is None or t.value_eur<min_eur):continue
     if not relevant('latvia',t.cpv,t.title+' '+t.description):continue
     stats['relevant']+=1;out.append(t)
   else:
    stats['index_requests']+=1;s=BeautifulSoup(r.text,'html.parser')
    for a in s.select('a[href]'):
     link=urljoin(str(r.url),a['href'])
     if urlparse(link).netloc=='open.iub.gov.lv' and '/data/notice' in link and link not in seen:q.append(link)
 if not stats['json_files']:raise RuntimeError('Latvia IUB: no JSON files discovered; '+str(stats))
 return out,stats
