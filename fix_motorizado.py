import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Fix bot 59 back to connector 17
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[59], {'connector_id': 17}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print('✅ Bot 59 (MOTORIZADO) → connector=17 restaurado')
else:
    print('❌ Error:', resp.json().get('error', {}))

# Verify
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[59]],
        'kwargs': {'fields': ['id', 'name', 'connector_id', 'active']}
    }
})
r = resp2.json()
if 'result' in r and r['result']:
    bot = r['result'][0]
    conn = bot.get('connector_id')
    if isinstance(conn, (list, tuple)):
        conn = conn[0]
    print(f'  Verificación: Bot 59: {bot["name"]} | connector={conn} | active={bot.get("active",True)}')
