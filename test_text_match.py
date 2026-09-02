import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def call(model, method, args, kwargs=None):
    if kwargs is None:
        kwargs = {}
    resp = session.post('https://latinbien.com/web/dataset/call_kw/' + model + '/' + method, json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs}
    })
    return resp.json()

# 1. Ver los campos del modelo acrux.chat.bot, especialmente text_match y text_type
resp = call('ir.model.fields', 'search_read', [
    [['model_id.model', '=', 'acrux.chat.bot'], ['name', 'in', ['text_match', 'text_type', 'match_mode']]]
], {'fields': ['name', 'field_description', 'ttype', 'selection']})
print('=== Campos de matching ===')
for f in resp.get('result', []):
    print(f'  {f["name"]} ({f.get("field_description","?")}) type={f.get("ttype","?")} selection={f.get("selection","")}')

# 2. Ver los valores de text_match y cualquier campo de tipo para los bots
resp = call('acrux.chat.bot', 'search_read', [[['id', 'in', [61, 62, 110, 111]]]],
    {'fields': ['id', 'name', 'text_match', 'sequence', 'use_loop']})
print('\n=== Bots y configuracion ===')
for b in resp.get('result', []):
    print(f'  {b["id"]} {b["name"]}: text_match={repr(b["text_match"])} seq={b.get("sequence")} use_loop={b.get("use_loop")}')

# 3. Ver TODOS los hijos de CATCHER (61) ordenados por sequence
resp = call('acrux.chat.bot', 'search_read', [[['parent_id', '=', 61]]],
    {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': [['sequence', 'asc']]})
print('\n=== Hijos de CATCHER (orden por sequence) ===')
for b in resp.get('result', []):
    print(f'  seq={b["sequence"]} ID={b["id"]} text_match={repr(b["text_match"])} {b["name"]}')

# 4. Ver TODOS los hijos de VALIDAR_CEDULA (62)
resp = call('acrux.chat.bot', 'search_read', [[['parent_id', '=', 62]]],
    {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': [['sequence', 'asc']]})
print('\n=== Hijos de VALIDAR_CEDULA (orden por sequence) ===')
for b in resp.get('result', []):
    print(f'  seq={b["sequence"]} ID={b["id"]} text_match={repr(b["text_match"])} {b["name"]}')

# 5. Ver TODOS los hijos de MENU_RECOMPRA (65)
resp = call('acrux.chat.bot', 'search_read', [[['parent_id', '=', 65]]],
    {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': [['sequence', 'asc']]})
print('\n=== Hijos de MENU_RECOMPRA (orden por sequence) ===')
for b in resp.get('result', []):
    print(f'  seq={b["sequence"]} ID={b["id"]} text_match={repr(b["text_match"])} {b["name"]}')
