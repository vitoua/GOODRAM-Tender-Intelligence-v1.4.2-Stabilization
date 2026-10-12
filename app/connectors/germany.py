import httpx,zipfile,io,json,re
from datetime import date,timedelta,datetime
from app.models import Tender
from app.filters import relevant,source_filter
from app.connectors.common import date_any,clean
URL='https://oeffentlichevergabe.de/api/notice-exports'
def releases(o):
 if isinstance(o,list):return o
 if isinstance(o,dict):return o.get('releases') or o.get('records') or o.get('data') or [o]
 return []
async def fetch(countries,start,min_eur):
 stats={'days':0,'files':0,'records':0,'after_date':0,'cpv_matches':0,'keyword_matches':0,'relevant':0,'errors':[]};out=[];f=source_filter('germany')
 async with httpx.AsyncClient(timeout=60,follow_redirects=True) as c:
  for offset in range(1,min(31,max(2,(date.today()-start.date()).days+1))):
   day=(date.today()-timedelta(days=offset)).isoformat();r=await c.get(URL,params={'pubDay':day,'format':'ocds.zip'});stats['days']+=1
   if r.status_code in (400,404):stats['errors'].append({'day':day,'status':r.status_code});continue
   r.raise_for_status();z=zipfile.ZipFile(io.BytesIO(r.content));stats['files']+=len(z.namelist())
   for n in z.namelist():
    if not n.endswith(('.json','.jsonl')):continue
    try:
     raw=z.read(n).decode('utf-8-sig');docs=[json.loads(x) for x in raw.splitlines() if x.strip()] if n.endswith('.jsonl') else [json.loads(raw)]
    except:continue
    for doc in docs:
     for d in releases(doc):
      stats['records']+=1;pub=date_any(d.get('date') or d.get('publishedDate'))
      if pub and pub<start:continue
      stats['after_date']+=1;t=d.get('tender') or {};title=clean(t.get('title'));desc=clean(t.get('description'));codes=[]
      for x in t.get('items') or []:
       cls=x.get('classification') or {}
       if cls.get('id'):codes.append(cls['id'])
      norm=[re.sub(r'\D','',x)[:8] for x in codes];stats['cpv_matches']+=int(any(x in f['codes'] for x in norm));stats['keyword_matches']+=int(any(k.casefold() in (title+' '+desc).casefold() for k in f['keywords']))
      if not relevant('germany',codes,title+' '+desc):continue
      deadline=date_any((t.get('tenderPeriod') or {}).get('endDate'))
      if deadline and deadline<datetime.now():continue
      pid=str(d.get('ocid') or d.get('id'));buyer=((d.get('buyer') or {}).get('name',''));url=d.get('url') or 'https://oeffentlichevergabe.de'
      out.append(Tender(pid,'germany','DEU',title,buyer,deadline=deadline,published=pub,url=url,description=desc,procurement_id=pid,cpv=codes,source_links={'Germany OCDS':url}));stats['relevant']+=1
 return out,stats
