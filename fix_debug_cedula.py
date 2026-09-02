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

# Add debug as the FIRST line after texto
old_first = "texto = (mess_id.text or '').strip()\nif texto == '6':"
new_first = "texto = (mess_id.text or '').strip()\nret = [{'send_text': 'DEBUG VALIDAR_CEDULA: texto=' + repr(texto)}]\nif texto == '6':"

if old_first in code:
    new_code = code.replace(old_first, new_first, 1)
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - DEBUG added to VALIDAR_CEDULA')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('Old first block not found')
    print('First 200 chars:', repr(code[:200]))
