import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read bot 74
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[74]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# Show each line with repr to see exact characters
print("=== Bot 74 code (repr each line) ===")
for i, line in enumerate(code.split('\n')):
    print(f'{i+1}: {repr(line)}')

# Check if the pattern exists
print("\n=== Looking for ret patterns ===")
for i, line in enumerate(code.split('\n')):
    if 'ret = [' in line:
        print(f'L{i+1}: {repr(line)}')
