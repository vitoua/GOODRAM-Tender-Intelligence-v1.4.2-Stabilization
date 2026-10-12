"""Parallel translation mechanisms.
V1 keeps optional LibreTranslate compatibility.
V2 uses Azure AI Translator, with a local JSON cache. No existing translations are removed.
"""
import json,time,uuid,hashlib
from pathlib import Path
import httpx
from app.config import settings
CACHE=Path('data/translations_v2.json');STATE={'translated':0,'failed':0,'last_error':'','last_translation':None}
def load():
 try:return json.loads(CACHE.read_text(encoding='utf-8'))
 except:return {}
def save(d):
 try:CACHE.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 except:pass
def status():
 d=load();return {'v1_legacy_enabled':bool(settings.libretranslate_url),'v2_provider':'azure' if settings.azure_translator_key else 'disabled','v2_enabled':bool(settings.azure_translator_key),'cache_records':len(d),'translated':STATE['translated'],'failed':STATE['failed'],'last_error':STATE['last_error'],'last_translation':STATE['last_translation']}
async def azure(texts,target):
 url='https://api.cognitive.microsofttranslator.com/translate'
 headers={'Ocp-Apim-Subscription-Key':settings.azure_translator_key,'Ocp-Apim-Subscription-Region':settings.azure_translator_region,'Content-Type':'application/json','X-ClientTraceId':str(uuid.uuid4())}
 async with httpx.AsyncClient(timeout=35) as c:
  r=await c.post(url,params={'api-version':'3.0','to':target},headers=headers,json=[{'text':x} for x in texts]);r.raise_for_status();return [x['translations'][0]['text'] for x in r.json()]
async def legacy(texts,target):
 if not settings.libretranslate_url:raise RuntimeError('Legacy LibreTranslate is not configured')
 out=[]
 async with httpx.AsyncClient(timeout=35) as c:
  for x in texts:
   p={'q':x,'source':'auto','target':target,'format':'text'}
   if settings.libretranslate_api_key:p['api_key']=settings.libretranslate_api_key
   r=await c.post(settings.libretranslate_url.rstrip('/')+'/translate',json=p);r.raise_for_status();out.append(r.json()['translatedText'])
 return out
async def translate_tender(t,lang,provider='v2'):
 if lang not in ('pl','uk','en','es'):return False
 key=t.source+':'+t.procurement_id+':'+lang+':'+hashlib.sha1((t.title+'\n'+t.description).encode()).hexdigest()[:12];cache=load()
 if key in cache:t.translations[lang]=cache[key];return True
 texts=[t.title or '',(t.description or '')[:4500]]
 try:
  if provider=='v2':
   if not settings.azure_translator_key:raise RuntimeError('Translator V2 requires AZURE_TRANSLATOR_KEY and AZURE_TRANSLATOR_REGION')
   vals=await azure(texts,lang)
  else:vals=await legacy(texts,lang)
  rec={'title':vals[0],'description':vals[1]};cache[key]=rec;save(cache);t.translations[lang]=rec;STATE.update(translated=STATE['translated']+1,last_error='',last_translation=time.strftime('%Y-%m-%d %H:%M:%S'));return True
 except Exception as e:STATE.update(failed=STATE['failed']+1,last_error=f'{type(e).__name__}: {e}');return False
async def translate_many(items,lang,provider='v2',limit=50):
 ok=0
 for t in list(items)[:limit]:ok+=int(await translate_tender(t,lang,provider))
 return ok
