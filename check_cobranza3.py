import requests, json, sys

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read bot 45 (NOT FOUND)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[45]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match']}
    }
})
b45 = resp.json()['result'][0]
print('BOT 45: ' + b45['name'])
print('  text_match: ' + str(b45.get('text_match')))
print('  Code lines:')
if b45['code']:
    for i, line in enumerate(b45['code'].split('\n')[:25]):
        print('    L' + str(i+1) + ': ' + line)
else:
    print('    (empty)')
