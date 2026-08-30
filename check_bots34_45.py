import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Bot 34
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[34]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match']}
    }
})
print('Bot 34:', json.dumps(resp.json(), indent=2)[:300])
print()

# Bot 45
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[45]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match']}
    }
})
print('Bot 45:', json.dumps(resp.json(), indent=2)[:500])
print()

# Get bot 45 code length
b45 = resp.json()['result'][0]
lines = b45['code'].split('\n')
print(f'Bot 45 code lines: {len(lines)}')
print(f'Line 1: {repr(lines[0])}')
print(f'Line 2: {repr(lines[1])}')
