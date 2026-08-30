import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def call(session, model, method, args=None, kwargs=None):
    if kwargs is None:
        kwargs = {}
    resp = session.post('https://latinbien.com/web/dataset/call_kw/' + model + '/' + method, json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs}
    })
    return resp.json()

# Cambiar los hijos "6" de los menus a dos acciones separadas
for mid, mname in [(65, 'MENU_RECOMPRA'), (66, 'MENU_LC_APROBADA'), 
                    (64, 'MENU_REGISTRADO'), (63, 'MENU_NO_REGISTRADO')]:
    resp = call(session, 'acrux.chat.bot', 'search_read',
        [[['parent_id', '=', mid], ['text_match', '=', '6']]],
        {'fields': ['id']}
    )
    kids = resp.get('result', [])
    if not kids:
        print(f'{mname}: no se encontro hijo')
        continue
    
    bid = kids[0]['id']
    # Two separate actions: first send_text, then goto_and_wait
    new_code = (
        "ret = [\n"
        "    {'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32 pulgadas)'},\n"
        "    {'goto_and_wait': '#BUSCAR_PRODUCTO'}\n"
        "]"
    )
    resp = call(session, 'acrux.chat.bot', 'write', [[bid], {'code': new_code}])
    ok = resp.get('result')
    print(f'{mname} (ID={bid}): {"OK" if ok else "FAIL: " + str(resp.get("error",{}).get("message","?"))}')

# Also update VALIDAR_CEDULA's "6" branch to two-step approach
print('\nActualizando VALIDAR_CEDULA...')
resp = call(session, 'acrux.chat.bot', 'read', [[62]], {'fields': ['code']})
code = resp['result'][0]['code']

old_6 = (
    "if texto == '6':\n"
    "    ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32 pulgadas)', 'goto_and_wait': '#BUSCAR_PRODUCTO'}]\n"
    "elif texto:"
)

new_6 = (
    "if texto == '6':\n"
    "    ret = [\n"
    "        {'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32 pulgadas)'},\n"
    "        {'goto_and_wait': '#BUSCAR_PRODUCTO'}\n"
    "    ]\n"
    "elif texto:"
)

if old_6 in code:
    code = code.replace(old_6, new_6)
    resp = call(session, 'acrux.chat.bot', 'write', [[62], {'code': code}])
    print('OK' if resp.get('result') else 'FAIL')
else:
    print('No se encontro el texto exacto para reemplazar')
    # Try to find what the actual code looks like
    for i, line in enumerate(code.split('\n')[:5]):
        print(f'  Line {i+1}: {repr(line)}')

print('\n--- PRUEBA ---')
print('Escribe "6" desde el menu')
print('Luego escribe "televisor"')
