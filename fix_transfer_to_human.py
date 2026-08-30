import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# Replace the non-text handler to transfer to human
old = "ret = [{'send_text': 'Recib\\u00ed tu archivo pero solo proceso mensajes de texto. Por favor escribe tu c\\u00e9dula o el n\\u00famero de la opci\\u00f3n deseada.'}]"
new = "ret = [{'send_text': 'He recibido tu archivo. Te transfiero con un asesor para ayudarte.'}, {'clear_catcher': True}]"

if old in code:
    print('Found old text - replacing')
    new_code = code.replace(old, new)
    
    # Verify syntax
    compile(new_code, '<string>', 'exec')
    print('Syntax OK')
    
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - File/image now transfers to human')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('Old text NOT found - searching around...')
    for i, line in enumerate(code.split('\n')):
        if 'Recib' in line or 'archivo' in line or 'ttype' in line:
            print(f'L{i+1}: {repr(line)}')
