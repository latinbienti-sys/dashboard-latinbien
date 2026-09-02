import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Crear handler
code = (
    "if mess_id.text.strip() == '6':\n"
    "    ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\")', 'goto_and_wait': '#BUSCAR_PRODUCTO'}]\n"
    "else:\n"
    "    ret = []"
)

resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/create', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'create',
        'args': [{
            'name': 'HANDLER_6',
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
print('Crear:', result)

# Si fallo, probar con text_match
if not result.get('result'):
    print('\nProbando con text_match=6...')
    code2 = "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\")', 'goto_and_wait': '#BUSCAR_PRODUCTO'}]"
    
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/create', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'create',
            'args': [{
                'name': 'CONSULTA_6',
                'parent_id': 61,
                'text_match': '6',
                'sequence': 1,
                'code': code2,
                'body_whatsapp': False,
                'active': True,
            }],
            'kwargs': {}
        }
    })
    result2 = resp2.json()
    print('Crear CONSULTA_6:', result2)
    
    if result2.get('result'):
        # Forzar sequence=1
        new_id = result2['result']
        session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[new_id], {'sequence': 1}],
                'kwargs': {}
            }
        })
        print(f'Sequence forzada a 1 para bot {new_id}')

# Ver hijos de CATCHER
resp3 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['parent_id', '=', 61]]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': [['sequence', 'asc']]}
    }
})
print('\nHijos de CATCHER:')
for b in resp3.json().get('result', []):
    print(f'  seq={b["sequence"]} ID={b["id"]} text_match={repr(b["text_match"])} {b["name"]}')
