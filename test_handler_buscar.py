import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Set BUSCAR_PRODUCTO code to test
code = "ret = [{'send_text': 'PRUEBA: BUSCAR_PRODUCTO handler se ejecuto!'}]"

resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {
        'model': 'acrux.chat.bot',
        'method': 'write',
        'args': [[101], {'code': code}],
        'kwargs': {}
    }
})
print('BUSCAR_PRODUCTO test code set:', resp.json().get('result'))

# Verify
resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {
        'model': 'acrux.chat.bot',
        'method': 'read',
        'args': [[101]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'code']}
    }
})
b = resp2.json()['result'][0]
print(f'text_match={repr(b["text_match"])}')
print(f'code={repr(b["code"])}')

print('\n--- PRUEBA ---')
print('Escribe "6" desde el menu')
print('Luego escribe CUALQUIER COSA (ej: "hola")')
print('Si ves "PRUEBA: BUSCAR_PRODUCTO handler se ejecuto!" -> el handler funciona')
print('Si NO ves nada -> goto_and_wait no navega a BUSCAR_PRODUCTO')
