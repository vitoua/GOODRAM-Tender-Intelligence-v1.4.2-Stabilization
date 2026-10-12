from datetime import datetime,timedelta
from io import BytesIO
import asyncio,traceback,hashlib,json
from fastapi import FastAPI,Form,Request,HTTPException
from fastapi.responses import JSONResponse,RedirectResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.store import store
from app.i18n import tr
from app.sources import COUNTRIES,NAMES,D
from app.filters import all_filters
from app.translate import translate_tender,translate_many,status as translator_status
app=FastAPI(version='1.4.2');app.mount('/static',StaticFiles(directory='app/static'),name='static');tpl=Jinja2Templates(directory='app/templates');JOB={'running':False,'progress':0,'message':''}
def lang(r):return r.cookies.get('lang') or settings.app_language
def ctx(r,x=None):return {'request':r,'lang':lang(r),'t':tr(lang(r)),'source_names':NAMES,'source_descriptions':D.get(lang(r),D['en']),'translator':translator_status(),**(x or {})}
def default_date():return (datetime.now()-timedelta(days=30)).date().isoformat()
@app.get('/health')
def health():return {'status':'ok','version':'1.4.2','tenders':len(store.data),'job':JOB,'translator':translator_status()}
@app.get('/lang/{code}')
def language(code,request:Request):
 r=RedirectResponse(request.headers.get('referer') or '/',303);r.set_cookie('lang',code if code in ('pl','uk','en','es') else 'pl');return r
@app.get('/')
def home(request:Request,q:str='',country:str='',source:str=''):
 rows=[x for x in store.data.values() if (not q or q.casefold() in (x.title+x.buyer+x.description).casefold()) and (not country or x.country==country) and (not source or x.source==source)];rows.sort(key=lambda x:x.deadline or datetime.max)
 return tpl.TemplateResponse(request=request,name='index.html',context=ctx(request,{'rows':rows,'countries':COUNTRIES,'default_date':default_date(),'runs':store.runs,'q':q,'country':country,'source':source,'last_update':store.last_update}))
async def execute(selected,sources,start,min_value):
 JOB.update(running=True,progress=2,message='Starting');plan=[]
 if 'ted' in sources:plan.append(('ted',[x for x in selected if x not in ('UKR','TUR')]))
 mapping={'prozorro':('prozorro','UKR'),'bzp':('bzp','POL'),'germany':('germany','DEU'),'ekap':('turkey','TUR'),'latvia':('latvia','LVA'),'nen':('nen','CZE'),'slovakia':('slovakia','SVK'),'cvpis':('cvpis','LTU'),'ekr':('ekr','HUN'),'estonia':('estonia','EST')}
 for shown,(mod,country) in mapping.items():
  if shown in sources and country in selected:plan.append((mod,[country]))
 results=[]
 for i,(mod,scope) in enumerate(plan,1):
  shown='ekap' if mod=='turkey' else mod;JOB.update(progress=int((i-1)/max(1,len(plan))*90)+5,message='Loading '+shown.upper())
  try:
   m=__import__('app.connectors.'+mod,fromlist=['fetch']);items,stats=await asyncio.wait_for(m.fetch(scope,start,min_value),240);results.append((shown,items,None,stats))
  except Exception as e:
   log=traceback.format_exc()[-2200:];results.append((shown,[],RuntimeError(f'{type(e).__name__}: {e} | log: {log}'),{'log_excerpt':log}))
 store.replace(results);JOB.update(running=False,progress=100,message='Complete')
@app.post('/refresh/start')
def start(countries:list[str]=Form(default=[]),sources:list[str]=Form(default=[]),min_value_eur:float=Form(0),published_from:str=Form('')):
 if JOB['running']:return JSONResponse({'message':'Refresh already running'},409)
 if not countries or not sources:return JSONResponse({'message':'Select country and source'},400)
 asyncio.create_task(execute(countries,sources,datetime.fromisoformat(published_from or default_date()),min_value_eur));return {'ok':True}
@app.get('/refresh/status')
def refresh_status():return JOB
@app.get('/tenders/{key:path}')
def detail(key,request:Request,view:str='translated'):
 x=next((v for v in store.data.values() if v.procurement_id==key),None)
 if not x:raise HTTPException(404)
 return tpl.TemplateResponse(request=request,name='detail.html',context=ctx(request,{'x':x,'view':view}))
@app.post('/translate/{key:path}')
async def translate_one(key,request:Request,provider:str=Form('v2')):
 x=next((v for v in store.data.values() if v.procurement_id==key),None)
 if not x:raise HTTPException(404)
 ok=await translate_tender(x,lang(request),provider);return JSONResponse({'ok':ok,'translator':translator_status()},200 if ok else 400)
@app.post('/translate-visible')
async def translate_visible(request:Request,ids:list[str]=Form(default=[]),provider:str=Form('v2')):
 wanted=[x for x in store.data.values() if not ids or x.procurement_id in ids];n=await translate_many(wanted,lang(request),provider,50);return {'ok':True,'translated':n,'translator':translator_status()}
@app.post('/translator/test')
async def translator_test(request:Request,provider:str=Form('v2')):
 from app.models import Tender
 x=Tender('test','test','', 'Solid-state drive procurement',description='Supply of enterprise storage devices',procurement_id='test-'+hashlib.md5(str(datetime.now()).encode()).hexdigest());ok=await translate_tender(x,lang(request),provider);return JSONResponse({'ok':ok,'result':x.translations.get(lang(request)),'translator':translator_status()},200 if ok else 400)
@app.get('/analytics')
def analytics(request:Request):return tpl.TemplateResponse(request=request,name='analytics.html',context=ctx(request,{'rows':list(store.data.values())}))
@app.get('/cpv')
def cpv(request:Request):return tpl.TemplateResponse(request=request,name='cpv.html',context=ctx(request,{'filters':all_filters()}))
@app.get('/keywords')
def keywords_page(request:Request):return tpl.TemplateResponse(request=request,name='keywords.html',context=ctx(request,{'filters':all_filters()}))
@app.get('/sources')
def sources_page(request:Request):return tpl.TemplateResponse(request=request,name='sources.html',context=ctx(request,{'runs':{x['source']:x for x in store.runs}}))
@app.get('/status')
def status_page(request:Request):return tpl.TemplateResponse(request=request,name='status.html',context=ctx(request,{'runs':{x['source']:x for x in store.runs}}))
@app.get('/about')
def about(request:Request):return tpl.TemplateResponse(request=request,name='about.html',context=ctx(request))
@app.get('/export.xlsx')
def export():
 from openpyxl import Workbook
 wb=Workbook();ws=wb.active;ws.title='Tenders';ws.append(['Source','Country','ID','Title','Buyer','Published','Deadline','Value','Currency','CPV','URL'])
 for x in store.data.values():ws.append([x.source,x.country,x.procurement_id,x.title,x.buyer,x.published,x.deadline,x.value,x.currency,', '.join(x.cpv),x.url])
 ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions;out=BytesIO();wb.save(out);out.seek(0);return StreamingResponse(out,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename="GOODRAM-Tender-Intelligence-v1.4.2.xlsx"'})
