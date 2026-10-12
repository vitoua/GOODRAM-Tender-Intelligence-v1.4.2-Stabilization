import httpx,re
from datetime import datetime
from app.models import Tender
from app.filters import source_filter
from app.connectors.common import clean,date_any
URL='https://api.ted.europa.eu/v3/notices/search'
FIELDS=['publication-number','notice-title','buyer-name','buyer-country','publication-date','deadline-receipt-tender-date-lot','classification-cpv','description-proc','estimated-value-proc','estimated-value-proc-currency']
def localized(v):
 if isinstance(v,str):return v
 if isinstance(v,list):return localized(v[0]) if v else ''
 if isinstance(v,dict):
  for k in ('eng','en','pol','pl','ukr','uk','deu','de','fra','fr','spa','es'):
   if v.get(k):return localized(v[k])
  return localized(next(iter(v.values()),''))
 return ''
def pick(d,*keys):
 for k in keys:
  if d.get(k) not in (None,'',[]):return d[k]
 return ''
async def fetch(countries,start,min_eur):
 f=source_filter('ted');stats={'queries':0,'scanned':0,'relevant':0,'unsupported_codes':0};out={}
 country=' OR '.join(f'buyer-country={c}' for c in countries)
 dateq=f'publication-date>={start.date().isoformat()}'
 queries=[]
 for i in range(0,len(f['codes']),8):queries.append(' OR '.join(f'classification-cpv={x}' for x in f['codes'][i:i+8]))
 queries.append(' OR '.join(f'FT~"{x}"' for x in f['keywords'][:10]))
 async with httpx.AsyncClient(timeout=55,follow_redirects=True,headers={'User-Agent':'GOODRAM-Tender-Intelligence/1.4.2'}) as c:
  for core in queries:
   q=f'({core}) AND ({dateq})'+(f' AND ({country})' if country else '')
   payload={'query':q,'page':1,'limit':100,'scope':'ACTIVE','onlyLatestVersions':True,'paginationMode':'PAGE_NUMBER','fields':FIELDS}
   r=await c.post(URL,json=payload);stats['queries']+=1
   if r.status_code>=400:
    txt=r.text
    bad=re.search(r"Value '([^']+)' is not supported",txt)
    if bad:stats['unsupported_codes']+=1;continue
    raise RuntimeError(f'TED HTTP {r.status_code}: {txt[:800]}')
   body=r.json();rows=body.get('notices') or body.get('results') or body.get('data') or []
   stats['scanned']+=len(rows)
   for d in rows:
    pid=str(pick(d,'publication-number','publicationNumber','id'));title=clean(localized(pick(d,'notice-title','title')));buyer=clean(localized(pick(d,'buyer-name','buyerName')));country_code=localized(pick(d,'buyer-country','country')) or ''
    if countries and country_code not in countries:continue
    deadline=date_any(localized(pick(d,'deadline-receipt-tender-date-lot','deadline')));pub=date_any(localized(pick(d,'publication-date','publicationDate')))
    if not deadline or deadline<datetime.now():continue
    desc=clean(localized(pick(d,'description-proc','description')));codes=re.findall(r'\b\d{8}\b',str(pick(d,'classification-cpv','cpv')))
    val=pick(d,'estimated-value-proc','value');cur=localized(pick(d,'estimated-value-proc-currency','currency')) or 'EUR'
    try:val=float(val) if val not in ('',None) else None
    except:val=None
    if min_eur and (cur!='EUR' or val is None or val<min_eur):continue
    url=f'https://ted.europa.eu/en/notice/-/detail/{pid}'
    out[pid]=Tender(pid,'ted',country_code,title,buyer,val,cur,deadline,pub,url,desc,pid,codes,val if cur=='EUR' else None,source_links={'TED':url});stats['relevant']+=1
 return list(out.values()),stats
