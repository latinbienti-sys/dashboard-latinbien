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

# CONSULTA bots con su handler correspondiente
CONSULTA_UPDATES = [
    (102, '#RECOMPRA_BUSCAR'),   # RECOMPRA_CONSULTA -> RECOMPRA_BUSCAR
    (103, '#LC_BUSCAR'),         # LC_CONSULTA -> LC_BUSCAR
    (104, '#REG_BUSCAR'),        # REG_CONSULTA -> REG_BUSCAR
    (105, '#NR_BUSCAR'),         # NR_CONSULTA -> NR_BUSCAR
]

print('=== Actualizando CONSULTA bots (sin write) ===')
for bot_id, handler_key in CONSULTA_UPDATES:
    # Codigo: SOLO send_text + goto_and_wait (sin write)
    code = (
        "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\")', 'goto_and_wait': '" + handler_key + "'}]"
    )
    
    resp = call('acrux.chat.bot', 'write', [[bot_id], {'code': code}])
    if resp.get('result'):
        print(f'  Bot {bot_id} -> OK (goto_and_wait: {handler_key})')
    else:
        print(f'  ERROR Bot {bot_id}: {resp.get("error",{}).get("message","???")}')

# Verificar
print('\n=== Verificacion ===')
for bot_id, _ in CONSULTA_UPDATES:
    resp = call('acrux.chat.bot', 'search_read', [[['id', '=', bot_id]]], {'fields': ['id', 'name', 'code']})
    b = resp.get('result', [])
    if b:
        print(f'{b[0]["id"]} {b[0]["name"]}:')
        print(f'  {b[0]["code"]}')
        print()
