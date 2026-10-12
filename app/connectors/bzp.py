import httpx
from datetime import datetime
from app.models import Tender
from app.filters import relevant
from app.connectors.common import date_any,clean
URL='https://ezamowienia.gov.pl/mo-board/api/v1/notice'
async def fetch(countries,start,min_eur):
 params={'NoticeType':'ContractNotice','PublicationDateFrom':start.strftime('%Y-%m-%dT00:00:00'),'PublicationDateTo':datetime.now().strftime('%Y-%m-%dT23:59:59'),'PageSize':100,'OrderType':'Delivery'};stats={'endpoint':URL,'params':params,'status':0,'response_excerpt':'','scanned':0,'relevant':0}
 async with httpx.AsyncClient(timeout=50,follow_redirects=True,headers={'User-Agent':'GOODRAM-Tender-Intelligence/1.4.2'}) as c:
  r=await c.get(URL,params=params);stats['status']=r.status_code;stats['response_excerpt']=clean(r.text)[:900]
  if r.status_code>=400:raise RuntimeError(f"BZP HTTP {r.status_code}; params={params}; response={stats['response_excerpt']}")
  body=r.json();rows=body if isinstance(body,list) else body.get('items') or body.get('data') or body.get('notices') or [];stats['scanned']=len(rows);out=[]
  for d in rows:
   title=clean(d.get('orderObject') or d.get('title'));desc=clean(d.get('htmlBody') or d.get('description'));codes=[]
   for x in d.get('cpvCodes') or d.get('cpv') or []:codes.append(x.get('code') if isinstance(x,dict) else str(x))
   if not relevant('bzp',codes,title+' '+desc):continue
   pid=str(d.get('noticeNumber') or d.get('objectId') or d.get('id'));url=d.get('noticeUrl') or 'https://ezamowienia.gov.pl/mo-client-board/bzp/notice-details/'+pid
   out.append(Tender(pid,'bzp','POL',title,d.get('organizationName',''),deadline=date_any(d.get('submittingOffersDate')),published=date_any(d.get('publicationDate')),url=url,description=desc,procurement_id=pid,cpv=codes,source_links={'BZP':url}));stats['relevant']+=1
 return out,stats
