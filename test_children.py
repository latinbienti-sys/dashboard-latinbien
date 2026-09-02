import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# 1. Todos los hijos de MENU_RECOMPRA (65) con su sequence
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['parent_id', '=', 65]]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': [['sequence', 'asc']]}
    }
})
print('=== HIJOS DE MENU_RECOMPRA (orden por sequence) ===')
for b in resp.json().get('result', []):
    print(f'  seq={b["sequence"]} | ID={b["id"]} | text_match={repr(b["text_match"])} | {b["name"]}')

# 2. Verificar el text_match exacto de CONSULTA
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['name', 'like', '%CONSULTA%']]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'parent_id', 'active']}
    }
})
print('\n=== BOTS CONSULTA ===')
for b in resp.json().get('result', []):
    pid = b.get('parent_id', ['', ''])
    print(f'  ID={b["id"]} text_match={repr(b["text_match"])} active={b.get("active")} parent={pid[1] if isinstance(pid, list) else pid}')
