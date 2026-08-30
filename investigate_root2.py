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

# Bot 61 completo
b61 = call('acrux.chat.bot', 'read', [[61]], {'fields': ['id','name','parent_id','text_match','sequence','bot_key','child_ids','code']})[0]
print('=== BOT 61 (CATCHER) ===')
print('  name:', b61['name'])
print('  parent_id:', b61['parent_id'])
print('  text_match:', b61['text_match'])
print('  sequence:', b61['sequence'])
print('  bot_key:', b61['bot_key'])
print('  child_ids:', b61['child_ids'])
print('  code (300):', (b61.get('code') or '')[:300].replace('\n',' '))

# Buscar SI existe algun bot con parent_id False en TODO el modelo (no solo conn 2)
any_root = call('acrux.chat.bot', 'search_read', [[('parent_id', '=', False)]], {'fields':['id','name','connector_id'], 'limit': 50})
print('\n=== TODOS los bots con parent_id=False (cualquier conector) ===')
print('  count:', len(any_root or []))
for b in (any_root or []):
    print('   ', b['id'], b['name'], 'conn=', b.get('connector_id'))

# Leer el conector 2 con todos los campos para ver el campo de catcher
conn = call('acrux.chat.connector', 'read', [[2]], {'fields': ['id','name','bot_log','thread_minutes','tz','company_id']})
print('\n=== CONECTOR 2 (read) ===')
print('  ', conn)

# Tambien intentar campo 'chatbot_id' si existe
try:
    conn2 = call('acrux.chat.connector', 'read', [[2]], {'fields': ['id','name','chatbot_id']})
    print('  chatbot_id:', conn2)
except Exception as e:
    print('  chatbot_id err:', e)
