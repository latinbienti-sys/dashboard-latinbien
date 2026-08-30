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

# Bots CONSULTA con su return_menu
CONSULTA_BOTS = [
    (102, '#MENU_RECOMPRA'),
    (103, '#MENU_LC_APROBADA'),
    (104, '#No tienes linea'),
    (105, '#Registro'),
]

for bot_id, return_menu in CONSULTA_BOTS:
    # Codigo con goto_and_wait en el MISMO dict que send_text
    # En la stored code, \n debe ser literal backslash-n (\\n en Python)
    code = (
        "conv = mess_id.contact_id\n"
        "conv.write({'note': 'return_menu=" + return_menu + "'})\n"
        "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\")', 'goto_and_wait': '#BUSCAR_PRODUCTO'}]"
    )
    
    resp = call('acrux.chat.bot', 'write', [[bot_id], {'code': code}])
    if resp.get('result'):
        print(f'Bot {bot_id} -> OK')
    else:
        print(f'Bot {bot_id} -> ERROR: {resp.get("error",{}).get("message","???")}')

# Verificar
print('\n--- Verificacion ---')
resp = call('acrux.chat.bot', 'search_read', [[['id', 'in', [102, 103, 104, 105]]]],
    {'fields': ['id', 'name', 'code']})
for b in resp.get('result', []):
    print(f'{b["id"]} {b["name"]}: code={b["code"][:180]}')
