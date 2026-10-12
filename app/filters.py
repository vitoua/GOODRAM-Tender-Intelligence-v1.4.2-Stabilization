import json,re
from pathlib import Path
P=Path('data/filters.json')
def all_filters():return json.loads(P.read_text(encoding='utf-8'))
def source_filter(s):return all_filters().get(s,{'codes':[],'keywords':[]})
def relevant(source,codes,text):
 f=source_filter(source);norm=[re.sub(r'\D','',str(x))[:8] for x in codes];allowed=[re.sub(r'\D','',x)[:8] for x in f.get('codes',[])]
 code_ok=any(c==a or (a.endswith('0000') and c.startswith(a.rstrip('0'))) for c in norm for a in allowed)
 t=(text or '').casefold();kw_ok=any(k.casefold() in t for k in f.get('keywords',[]))
 return code_ok or kw_ok
