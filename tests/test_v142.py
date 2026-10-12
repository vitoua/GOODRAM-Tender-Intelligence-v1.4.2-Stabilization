import json,hashlib,pathlib
from app.main import app
from app.sources import NAMES,D
from app.filters import all_filters
from app.translate import status
required={'ted','prozorro','latvia','ekap','bzp','germany','nen','slovakia','cvpis','ekr','estonia'}
assert app.version=='1.4.2'
assert required<=set(NAMES) and required<=set(all_filters())
locks=json.load(open('CONNECTOR_HASHES.json'))
for _,meta in locks.items():assert hashlib.sha256(pathlib.Path(meta['file']).read_bytes()).hexdigest()==meta['sha256']
for lang in ('pl','uk','en','es'):assert required<=set(D[lang])
assert status()['v2_provider'] in ('azure','disabled')
print('v1.4.2 tests ok')
