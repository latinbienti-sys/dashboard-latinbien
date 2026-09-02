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

# 1) Bots raiz (parent_id = False) en conector 2
roots = call('acrux.chat.bot', 'search_read', [[('connector_id', '=', 2), ('parent_id', '=', False)]],
            {'fields': ['id','name','text_match','sequence','bot_key','child_ids','code'], 'order':'sequence'})
print('=== BOTS RAIZ (parent_id=False) conector 2 ===')
for b in roots:
    print(f"  [{b['id']}] seq={b.get('sequence')} tm={str(b.get('text_match'))[:25]!r} key={b.get('bot_key')!r} hijos={b.get('child_ids')} {b['name'][:40]}")
    print('      code:', (b.get('code') or '')[:200].replace('\n',' '))

# 2) bot 62 (el catcher que valida cedula) - su parent y text_match
b62 = call('acrux.chat.bot', 'read', [[62]], {'fields': ['id','name','parent_id','text_match','sequence','bot_key']})[0]
print('\n=== BOT 62 ===')
print('  ', b62)

# 3) Conector 2 - campos de catcher
conn = call('acrux.chat.connector', 'search_read', [[('id','=',2)]],
            {'fields': ['id','name','chatbot_id','bot_log','thread_minutes','tz']})
print('\n=== CONECTOR 2 ===')
print('  ', conn)

# 4) Donde cuelga el catcher raiz (el parent de los roots, si lo tienen)
for b in roots:
    pid = b.get('parent_id')
    print(f"  root {b['id']} parent_id={pid}")
