import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Leer el codigo completo de VALIDAR_CEDULA (62)
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['id', '=', 62]]],
        'kwargs': {'fields': ['id', 'name', 'code', 'body_whatsapp']}
    }
})
bot = resp.json().get('result', [])
if bot:
    b = bot[0]
    code = b.get('code', '')
    body = b.get('body_whatsapp', '')
    print(f'ID={b["id"]} {b["name"]}')
    print(f'Code length: {len(code)}')
    print(f'Body length: {len(body) if body else 0}')
    # Guardar a archivo
    with open('c:/users/yarleyc/documents/new opencode project/validar_cedula_code.txt', 'w', encoding='utf-8') as f:
        f.write(code)
    with open('c:/users/yarleyc/documents/new opencode project/validar_cedula_body.txt', 'w', encoding='utf-8') as f:
        f.write(body or '')
    # Mostrar primeros 2000 chars
    print('\n--- CODE (primeros 2000 chars) ---')
    print(code[:2000])
else:
    print('Bot 62 not found')

# Tambien leer el body de CATCHER
resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['id', '=', 61]]],
        'kwargs': {'fields': ['id', 'name', 'body_whatsapp']}
    }
})
bot2 = resp2.json().get('result', [])
if bot2:
    print(f'\n--- CATCHER body ---')
    print(bot2[0].get('body_whatsapp', '')[:500])
