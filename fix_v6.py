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

# =========================================================
# 1. ACTUALIZAR VALIDAR_CEDULA - agregar opcion 6 a menu no registrados
# =========================================================
print('1. Actualizando VALIDAR_CEDULA (menu no registrado)...')
# Leer codigo actual
resp = call(session, 'acrux.chat.bot', 'read', [[62]], {'fields': ['code']})
code = resp['result'][0]['code']

# Reemplazar el texto del menu no registrado (sin opcion 6)
old_menu = (
    'msg = \'No encontr\\u00e9 tu c\\u00e9dula. \\u00bfEres nuevo?'
    '\\n\\nElige una opci\\u00f3n:'
    '\\n1\\ufe0f\\u20e3 Registrarme y solicitar LC'
    '\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo'
    '\\n3\\ufe0f\\u20e3 Compra de contado'
    '\\n4\\ufe0f\\u20e3 Reportar problema'
    '\\n5\\ufe0f\\u20e3 Consultar precio de producto\''
)

new_menu = (
    'msg = \'No encontr\\u00e9 tu c\\u00e9dula. \\u00bfEres nuevo?'
    '\\n\\nElige una opci\\u00f3n:'
    '\\n1\\ufe0f\\u20e3 Registrarme y solicitar LC'
    '\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo'
    '\\n3\\ufe0f\\u20e3 Compra de contado'
    '\\n4\\ufe0f\\u20e3 Reportar problema'
    '\\n5\\ufe0f\\u20e3 Consultar precio de producto'
    '\\n6\\ufe0f\\u20e3 Consultar precio de producto\''
)

if old_menu in code:
    code = code.replace(old_menu, new_menu)
    resp = call(session, 'acrux.chat.bot', 'write', [[62], {'code': code}])
    print('  OK' if resp.get('result') else '  FAIL: ' + str(resp.get('error',{}).get('message','')))
else:
    print('  No se encontro el texto del menu no registrado (puede que ya este actualizado)')

# =========================================================
# 2. ACTUALIZAR los hijos "6" de cada menu para incluir send_text
# =========================================================
print('\n2. Actualizando hijos "6" de los menus...')

for mid, mname in [(65, 'MENU_RECOMPRA'), (66, 'MENU_LC_APROBADA'), 
                    (64, 'MENU_REGISTRADO'), (63, 'MENU_NO_REGISTRADO')]:
    # Buscar el hijo text_match="6"
    resp = call(session, 'acrux.chat.bot', 'search_read',
        [[['parent_id', '=', mid], ['text_match', '=', '6']]],
        {'fields': ['id', 'name']}
    )
    kids = resp.get('result', [])
    if not kids:
        print(f'  {mname}: no se encontro hijo "6"')
        continue
    
    bot_id = kids[0]['id']
    # Actualizar codigo para incluir send_text
    new_code = (
        "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32 pulgadas)', "
        "'goto_and_wait': '#BUSCAR_PRODUCTO'}]"
    )
    resp = call(session, 'acrux.chat.bot', 'write', [[bot_id], {'code': new_code}])
    if resp.get('result'):
        print(f'  {mname} (ID={bot_id}): OK')
    else:
        err = resp.get('error', {}).get('message', '?')
        print(f'  {mname} (ID={bot_id}): ERROR - {err}')

# =========================================================
# 3. VERIFICACION
# =========================================================
print('\n3. Verificando...')
resp = call(session, 'acrux.chat.bot', 'read', [[62]], {'fields': ['code']})
code = resp['result'][0]['code']
# Find the "No encontré tu cédula" msg
for line in code.split('\n'):
    if 'No encontr' in line and 'Elige' in line:
        print(f'  Menu no registrado: {line[:80]}...')
        break
# Also check if 6 appears in that line
if '6\\ufe0f' in code or '\\n6\\ufe0f' in code:
    print('  Opcion 6 presente en menu no registrado: SI')
else:
    print('  Opcion 6 presente en menu no registrado: NO')

print('\n--- PRUEBA ---')
print('Desde el menu, escribe "6"')
print('Deberias ver: "Escribe el nombre del producto..."')
print('Luego escribe un producto (ej: nevera)')
