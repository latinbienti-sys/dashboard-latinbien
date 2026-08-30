# -*- coding: utf-8 -*-
import requests, sys, datetime
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
API = 'https://latinbien.com/web/dataset/call_kw'

# Buscar mensajes entrantes que parezcan imagen/archivo en los ultimos 30 dias
since = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
r = s.post(f'{API}/acrux.chat.message/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.message', 'method': 'search_read',
        'args': [[('create_date', '>=', since), ('from_me', '=', False)]],
        'kwargs': {'fields': ['id', 'text', 'ttype', 'create_date', 'contact_id'],
            'order': 'create_date desc', 'limit': 200}}
}).json().get('result') or []

print(f'Total entrantes en 30 dias: {len(r)}')
from collections import Counter
cnt = Counter(m.get('ttype') or 'text' for m in r)
print('Por ttype:', dict(cnt))

# Mostrar los no-text y textos raros (con nombres de archivo, rutas, extensiones)
import re
print('\n=== No-text o con extension de archivo ===')
for m in r:
    ttype = m.get('ttype')
    txt = str(m.get('text') or '')
    es_archivo = bool(re.search(r'\.(pdf|png|jpg|jpeg|webp|heic|docx?|xlsx?|txt|zip)\b', txt, re.I)) or bool(re.search(r'(image|file|document|attachment)', txt, re.I)) or 'adjunto' in txt.lower()
    if ttype != 'text' or es_archivo:
        print(f"  [{m.get('create_date','')[:19]}] id={m['id']} ttype={ttype} text={txt[:120]!r}")
