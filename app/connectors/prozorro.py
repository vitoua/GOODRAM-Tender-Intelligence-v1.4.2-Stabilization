import asyncio,httpx
from datetime import datetime
from app.models import Tender
from app.filters import relevant
from app.connectors.common import date_any
BASE='https://public-api.prozorro.gov.ua/api/2.5'
ACTIVE={'active.enquiries','active.tendering','active.auction','active.qualification','active.awarded'}
async def fetch(countries,start,min_eur):
 stats={'pages':0,'scanned':0,'details_ok':0,'after_date':0,'active':0,'relevant':0};refs=[]
 async with httpx.AsyncClient(timeout=35,follow_redirects=True,headers={'User-Agent':'GOODRAM-Tender-Intelligence/1.4.2'}) as c:
  url=BASE+'/tenders';params={'limit':100,'descending':1}
  for _ in range(20):
   r=await c.get(url,params=params);r.raise_for_status();b=r.json();page=b.get('data',[]);refs+=page;stats['pages']+=1;stats['scanned']+=len(page)
   nxt=(b.get('next_page') or {}).get('uri');
   if not nxt or not page:break
   url=nxt;params=None
  sem=asyncio.Semaphore(20)
  async def load(x):
   async with sem:
    try:
     r=await c.get(BASE+'/tenders/'+x['id']);r.raise_for_status();return r.json().get('data',{})
    except:return None
  details=await asyncio.gather(*(load(x) for x in refs));out=[]
  for d in filter(None,details):
   stats['details_ok']+=1;pub=date_any(d.get('dateCreated') or d.get('dateModified'))
   if pub and pub<start:continue
   stats['after_date']+=1;deadline=date_any((d.get('tenderPeriod') or {}).get('endDate'))
   if d.get('status') not in ACTIVE or not deadline or deadline<datetime.now():continue
   stats['active']+=1;items=d.get('items') or [];codes=[]
   for i in items:
    cls=i.get('classification') or {}
    if cls.get('id'):codes.append(cls['id'])
   text=' '.join([d.get('title',''),d.get('description','')]+[i.get('description','') for i in items])
   if not relevant('prozorro',codes,text):continue
   val=d.get('value') or {};amount=val.get('amount');cur=val.get('currency','UAH')
   if min_eur>0 and cur=='EUR' and (amount is None or amount<min_eur):continue
   tid=d.get('tenderID') or d.get('id');url='https://prozorro.gov.ua/tender/'+tid
   out.append(Tender(d['id'],'prozorro','UKR',d.get('title',''),(d.get('procuringEntity') or {}).get('name',''),amount,cur,deadline,pub,url,d.get('description',''),tid,codes,amount if cur=='EUR' else None,source_links={'Prozorro':url}));stats['relevant']+=1
 return out,stats
