import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Crear handler con codigo simple
code = (
    "if mess_id.text.strip() == '6':\n"
    "    ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\\\")', 'goto_and_wait': '#BUSCAR_PRODUCTO'}]\n"
    "else:\n"
    "    ret = []\n"
)

resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/create', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'create',
        'args': [{
            'name': 'HANDLER_OPCION6',
            'parent_id': 61,
            'text_match': False,
            'sequence': 1,
            'code': code,
            'body_whatsapp': False,
            'active': True,
        }],
        'kwargs': {}
    }
})
result = resp.json()
print('Crear handler:', result.get('result'))
if not result.get('result'):
    print('Error:', result.get('error', {}).get('message', '?'))

# Ver hijos de CATCHER
resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['parent_id', '=', 61]]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': [['sequence', 'asc']]}
    }
})
print('\nHijos de CATCHER:')
for b in resp2.json().get('result', []):
    print(f'  seq={b["sequence"]} ID={b["id"]} text_match={repr(b["text_match"])} {b["name"]}')
