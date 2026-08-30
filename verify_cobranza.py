# -*- coding: utf-8 -*-
import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
API = 'https://latinbien.com/web/dataset/call_kw'
def call(model, method, args, kwargs=None):
    resp = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return resp.json().get('result')

bots = call('acrux.chat.bot', 'search_read', [[('id', 'in', [40, 41, 45, 46])]],
            {'fields': ['id', 'name', 'code']})
by_id = {b['id']: b for b in (bots or [])}

print('=== BOT 40 (primeros 400 chars) ===')
print((by_id.get(40) or {}).get('code', '')[:400])
print('\n=== BOT 41 (ultimos 600 chars) ===')
print((by_id.get(41) or {}).get('code', '')[-600:])
print('\n=== BOT 45 ===')
print((by_id.get(45) or {}).get('code', '')[:300])
print('\n=== BOT 46 EXIT ===')
print((by_id.get(46) or {}).get('code', ''))

# Verificar si existe la key #MENUINICIAL
allb = call('acrux.chat.bot', 'search_read', [[]], {'fields': ['id', 'name', 'bot_key']})
keys = {b.get('bot_key') for b in (allb or []) if b.get('bot_key')}
print('\n=== KEYS EXISTENTES ===')
print(sorted(keys))
print('MENUINICIAL existe:', '#MENUINICIAL' in keys)
