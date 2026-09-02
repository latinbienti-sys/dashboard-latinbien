import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Buscar hijos de MENU_RECOMPRA por nombre
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['parent_id', '!=', False], ['name', 'not like', '%COBRANZA%'], ['name', 'not like', '%CONECTOR%']]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'parent_id'], 'limit': 30}
    }
})
print('Todos los bots (no cobranza):')
for b in resp.json().get('result', []):
    pid = b.get('parent_id', ['', ''])
    pid_name = pid[1] if isinstance(pid, list) else str(pid)
    print(f'  ID={b["id"]:>4} text_match={repr(b["text_match"]):>8} parent_id={pid[0] if isinstance(pid, list) else pid} -> {pid_name[:50]}')

# Buscar todos los que mencionen RECOMPRA o CONSULTA
print('\n--- Bots con RECOMPRA o CONSULTA en nombre ---')
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['name', 'in', ['RECOMPRA_CONSULTA', 'RECOMPRA_BUSCAR', 'RECOMPRA_CREDITO']]]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'parent_id', 'active', 'sequence']}
    }
})
for b in resp.json().get('result', []):
    pid = b.get('parent_id', ['', ''])
    pid_name = pid[1] if isinstance(pid, list) else str(pid)
    print(f'  ID={b["id"]:>4} {b["name"]:<25} text_match={repr(b["text_match"]):>8} seq={b.get("sequence")} active={b.get("active")} parent={pid_name[:50]}')
