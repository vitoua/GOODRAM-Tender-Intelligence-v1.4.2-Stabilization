import httpx,re
from app.connectors.common import excerpt
BASE='https://viesiejipirkimai.lt';PATHS=['/epps/cft/listContractDocuments.do','/epps/cft/prepareViewCfTWS.do','/epps/cft/listContractNotice.do']
async def fetch(countries,start,min_eur):
 stats={'attempts':[],'ids':0};ids=set()
 async with httpx.AsyncClient(timeout=40,follow_redirects=True) as c:
  for p in PATHS:
   try:r=await c.get(BASE+p);stats['attempts'].append({'path':p,'status':r.status_code,'bytes':len(r.content),'excerpt':excerpt(r.text,300)});ids.update(re.findall(r'resourceId=(\d+)',r.text))
   except Exception as e:stats['attempts'].append({'path':p,'error':str(e)})
 stats['ids']=len(ids)
 if not ids:raise RuntimeError('CVP IS discovery returned 0 resourceIds; '+str(stats))
 return [],stats
