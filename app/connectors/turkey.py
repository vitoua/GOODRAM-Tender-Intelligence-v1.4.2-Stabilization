import httpx
from app.config import settings
from app.models import Tender
from app.connectors.common import date_any
ACTOR='atisaysekerci~turkey-tenders-ekap'
async def fetch(countries,start,min_eur):
 if not settings.apify_api_token:raise RuntimeError('APIFY_API_TOKEN is not configured')
 url=f'https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items'
 payload={'maxItems':100,'keywords':['SSD','NVMe','RAM','DRAM','server','depolama']}
 async with httpx.AsyncClient(timeout=180) as c:
  r=await c.post(url,params={'token':settings.apify_api_token},json=payload);r.raise_for_status();rows=r.json()
 out=[]
 for i,d in enumerate(rows):
  pid=str(d.get('id') or d.get('tenderNo') or i);title=d.get('title') or d.get('name') or '';link=d.get('url') or d.get('link') or ''
  out.append(Tender(pid,'ekap','TUR',title,d.get('buyer',''),deadline=date_any(d.get('deadline')),published=date_any(d.get('publicationDate')),url=link,description=d.get('description',''),procurement_id=pid,source_links={'EKAP':link}))
 return out,{'scanned':len(rows),'relevant':len(out)}
