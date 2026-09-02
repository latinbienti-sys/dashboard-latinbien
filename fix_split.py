import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Read current code
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# Old block to replace
old = ("if texto.startswith('6 '):\n"
       "    query = texto[2:].strip()\n"
       "    if query:")

new = ("parts = texto.split(None, 1)\n"
       "if len(parts) == 2 and parts[0] == '6':\n"
       "    query = parts[1]\n"
       "    if query:")

if old in code:
    new_code = code.replace(old, new, 1)
    # Write
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - Code updated with split() approach')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('Old block not found!')
    # Debug: find similar content
    if 'startswith' in code:
        for line in code.split('\n'):
            if 'startswith' in line:
                print('  Found:', repr(line))
        # Show the exact text around "if texto"
        idx = code.find('if texto')
        print('Context:', repr(code[idx:idx+150]))
    else:
        print('No startswith found in code at all')
        print('First 200 chars:', repr(code[:200]))
