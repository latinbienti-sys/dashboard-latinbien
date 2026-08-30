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

# Replace the split approach with a simpler one:
# Just check first char == '6' and rest is not empty after strip
old = ("parts = texto.split(None, 1)\n"
       "if len(parts) == 2 and parts[0] == '6':\n"
       "    query = parts[1]\n"
       "    if query:")

new = ("if len(texto) > 1 and texto[0] == '6':\n"
       "    query = texto[1:].strip()\n"
       "    if query:")

if old in code:
    new_code = code.replace(old, new, 1)
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - Code updated with simple first-char check')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('Old block not found!')
    # Show what we have
    if 'split' in code:
        idx = code.find('split')
        print('Current split code:', repr(code[idx:idx+80]))
    elif 'len(texto)' in code:
        print('Already has len check')
    else:
        print('Neither found. First 300 chars:', repr(code[:300]))
