import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def read_code(bot_id):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bot_id]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    return resp.json()['result'][0]['code']

def write_code(bot_id, code):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bot_id], {'code': code}], 'kwargs': {}
        }
    })
    return resp.json()

# ==========================================
# 1. Update CONSULTA_PRECIO_6 bots (118-121)
#    Change the instruction to clarify "6 + producto"
# ==========================================
NEW_INSTRUCTION = "ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 nevera'}]"

for bid in [118, 119, 120, 121]:
    code = read_code(bid)
    # Replace whatever code is there with the new instruction
    result = write_code(bid, NEW_INSTRUCTION)
    if result.get('result'):
        print('CONSULTA_PRECIO_6 (ID={}): OK'.format(bid))
    else:
        print('CONSULTA_PRECIO_6 (ID={}): FAIL'.format(bid))

# ==========================================
# 2. Update the menu text in VALIDAR_CEDULA (62)
#    Change option 6 to say "Consultar precio (escribe 6 + nombre)"
# ==========================================
code62 = read_code(62)

# Find the 4 menu texts and update option 6
# Current: 6\ufe0f\u20e3 Consultar precio de producto
# New:     6\ufe0f\u20e3 Consultar precio (escribe 6 + nombre)

old_menu_6 = '6\ufe0f\u20e3 Consultar precio de producto'
new_menu_6 = '6\ufe0f\u20e3 Consultar precio (escribe 6 + nombre)'

if old_menu_6 in code62:
    code62 = code62.replace(old_menu_6, new_menu_6)
    # Also update the "No encontré tu cédula" menu (has 2x option 6, one is wrong)
    # Fix the duplicate 6 in NO REGISTRADO menu
    old_nr_dup = '5\ufe0f\u20e3 Consultar precio de producto\n6\ufe0f\u20e3 Consultar precio de producto'
    new_nr_dup = '5\ufe0f\u20e3 Ver catalogo\n6\ufe0f\u20e3 Consultar precio (escribe 6 + nombre)'
    if old_nr_dup in code62:
        code62 = code62.replace(old_nr_dup, new_nr_dup)
        print('Fixed duplicate option 6 in NR menu')
    
    result = write_code(62, code62)
    if result.get('result'):
        print('VALIDAR_CEDULA (ID=62): OK - menu updated')
    else:
        print('VALIDAR_CEDULA (ID=62): FAIL - {}'.format(result.get('error', {})))
else:
    print('Could not find old menu text in VALIDAR_CEDULA')
    # Search for what's there
    idx = code62.find('Consultar precio')
    if idx >= 0:
        print('Found at', idx, ':', repr(code62[idx:idx+100]))

# ==========================================
# 3. Update the MENU variable at the bottom of BUSCAR_EN_* handlers
# ==========================================
# For handlers 122-124 (base menu)
old_menu_var = "Consultar precio de un producto."
new_menu_var = "Consultar precio (escribe 6 + nombre)"

for bid in [122, 123, 124]:
    code = read_code(bid)
    if old_menu_var in code:
        code = code.replace(old_menu_var, new_menu_var)
        result = write_code(bid, code)
        if result.get('result'):
            print('{} (ID={}): OK - menu var updated'.format('BUSCAR_EN_*', bid))
        else:
            print('{} (ID={}): FAIL'.format('BUSCAR_EN_*', bid))
    else:
        print('Handler {}: menu var not found'.format(bid))

# Handler 125 (NR menu) - different menu text
code125 = read_code(125)
old_nr_menu = "Consultar precio de un producto."
if old_nr_menu in code125:
    code125 = code125.replace(old_nr_menu, new_menu_var)
    result = write_code(125, code125)
    if result.get('result'):
        print('BUSCAR_EN_NR (ID=125): OK - menu var updated')
    else:
        print('BUSCAR_EN_NR (ID=125): FAIL')
else:
    print('Handler 125: menu var not found')
    print('Searching for Consultar...')
    idx = code125.find('Consultar')
    if idx >= 0:
        print('Found:', repr(code125[idx:idx+80]))
