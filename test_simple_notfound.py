import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Simple test code - just send a basic text message
simple_code = "ret = [{'send_text': 'Hola, soy LatinBot. Escribe 1, 2, 3, 4, 5 o #'}]"

# Write to bot 45
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[45], {'code': simple_code}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print('OK - Codigo simple escrito en Bot 45')
else:
    print('ERROR:', resp.json().get('error', {}))

# Verify
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[45]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b45 = resp2.json()['result'][0]
print(f'Codigo actual: {repr(b45["code"])}')
