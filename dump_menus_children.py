# -*- coding: utf-8 -*-
import requests, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)
s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
API = 'https://latinbien.com/web/dataset/call_kw'
def call(model, method, args, kwargs=None):
    r = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return r.json().get('result')

for mid in [63, 64, 65, 66]:
    b = call('acrux.chat.bot', 'read', [[mid]], {'fields': ['id','name','bot_key','child_ids']})[0]
    print(f"\n##### MENU {mid}: {b['name']}  key={b.get('bot_key')}  hijos={b.get('child_ids')}")
    kids = call('acrux.chat.bot', 'search_read', [[('id','in', b['child_ids'])]],
                {'fields': ['id','name','text_match','sequence','bot_key','code'], 'order':'sequence'})
    for k in kids:
        c = k.get('code') or ''
        es_precio = any(x in c for x in ['Resultados para','list_price','Precio:'])
        print(f"   [{k['id']}] seq={k.get('sequence')} tm={str(k.get('text_match'))[:20]!r} key={k.get('bot_key')!r} precio={es_precio}  {k['name'][:35]}")
