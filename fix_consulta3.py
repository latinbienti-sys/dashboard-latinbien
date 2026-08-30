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

# Codigo para los handlers de busqueda (usando \\n literal para stored code)
# En Python, '\\n' es backslash-n (2 chars), se almacena como \n y safe_eval lo interpreta como newline
CODIGO_BUSCAR = (
    "try:\n"
    "    query = mess_id.text.strip()\n"
    "    Product = env['product.template']\n"
    "    products = Product.search([('name', 'ilike', '%' + query + '%')], limit=3)\n"
    "    if products:\n"
    "        lines = ['Resultados para: ' + query + '\\n']\n"
    "        for p in products:\n"
    "            precio = p.list_price\n"
    "            if precio and precio > 0:\n"
    "                inicial = round(precio * 0.30, 2)\n"
    "                cuota = round((precio - inicial) / 20, 2)\n"
    "                lines.append(p.name)\n"
    "                lines.append('Precio: $' + '{:.2f}'.format(precio))\n"
    "                lines.append('Inicial (30%): $' + '{:.2f}'.format(inicial))\n"
    "                lines.append('20 cuotas de: $' + '{:.2f}'.format(cuota))\n"
    "                lines.append('')\n"
    "            else:\n"
    "                lines.append(p.name + ' - Consultar precio en tienda')\n"
    "                lines.append('')\n"
    "        lines.append('Catalogo: https://latinbien.com/shop/')\n"
    "        msg = '\\n'.join(lines)\n"
    "    else:\n"
    "        msg = 'No encontre productos con \"' + query + '\".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/'\n"
    "except Exception as e:\n"
    "    msg = 'Error al buscar: ' + str(e)\n"
    "\n"
    "ret = [{'send_text': msg, 'goto_and_wait': 'MENU_KEY'}]\n"
)

# Crear handlers de busqueda bajo cada menu
BUSCAR_HANDLERS = [
    {'parent_id': 65, 'name': 'RECOMPRA_BUSCAR', 'bot_key': '#RECOMPRA_BUSCAR', 'return_menu': '#MENU_RECOMPRA'},
    {'parent_id': 66, 'name': 'LC_BUSCAR', 'bot_key': '#LC_BUSCAR', 'return_menu': '#MENU_LC_APROBADA'},
    {'parent_id': 64, 'name': 'REG_BUSCAR', 'bot_key': '#REG_BUSCAR', 'return_menu': '#No tienes linea'},
    {'parent_id': 63, 'name': 'NR_BUSCAR', 'bot_key': '#NR_BUSCAR', 'return_menu': '#Registro'},
]

print('=== Creando handlers de busqueda ===')
handler_map = {}
for bot in BUSCAR_HANDLERS:
    code = CODIGO_BUSCAR.replace('MENU_KEY', bot['return_menu'])
    
    resp = call('acrux.chat.bot', 'create', [{
        'name': bot['name'],
        'parent_id': bot['parent_id'],
        'text_match': False,
        'bot_key': bot['bot_key'],
        'code': code,
        'body_whatsapp': False,
        'active': True,
    }])
    hid = resp.get('result')
    if hid:
        handler_map[bot['parent_id']] = {'id': hid, 'key': bot['bot_key']}
        print(f'  {bot["name"]} (ID={hid}) bot_key={bot["bot_key"]}')
    else:
        print(f'  ERROR {bot["name"]}: {resp.get("error",{}).get("message","???")}')

# Codigo para los CONSULTA bots (goto_and_wait al handler especifico + send_text en mismo dict)
# Mapeo de menu parent_id -> handler bot_key
MENU_HANDLER = {
    65: '#RECOMPRA_BUSCAR',  # MENU_RECOMPRA
    66: '#LC_BUSCAR',        # MENU_LC_APROBADA
    64: '#REG_BUSCAR',       # MENU_REGISTRADO
    63: '#NR_BUSCAR',        # MENU_NO_REGISTRADO
}

# CONSULTA bots existentes y su parent_id
CONSULTA_INFO = [
    (102, 65, '#MENU_RECOMPRA'),
    (103, 66, '#MENU_LC_APROBADA'),
    (104, 64, '#No tienes linea'),
    (105, 63, '#Registro'),
]

print('\n=== Actualizando CONSULTA bots ===')
for bot_id, parent_id, return_menu in CONSULTA_INFO:
    handler_key = MENU_HANDLER.get(parent_id)
    if not handler_key:
        print(f'  Bot {bot_id}: no handler, skip')
        continue
    
    code = (
        "conv = mess_id.contact_id\n"
        "conv.write({'note': 'return_menu=" + return_menu + "'})\n"
        "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\")', 'goto_and_wait': '" + handler_key + "'}]"
    )
    
    resp = call('acrux.chat.bot', 'write', [[bot_id], {'code': code}])
    if resp.get('result'):
        print(f'  Bot {bot_id} -> goto_and_wait: {handler_key}')
    else:
        print(f'  ERROR Bot {bot_id}: {resp.get("error",{}).get("message","???")}')

print('\n=== Verificacion ===')
for parent_id, info in handler_map.items():
    resp = call('acrux.chat.bot', 'search_read', [[['id', '=', info['id']]]], {'fields': ['id', 'name', 'bot_key', 'text_match', 'code']})
    b = resp.get('result', [])
    if b:
        print(f'\n{b[0]["id"]} {b[0]["name"]}:')
        print(f'  bot_key={b[0]["bot_key"]} text_match={b[0]["text_match"]}')
        print(f'  code: {b[0]["code"][:150]}...')

print('\n=== LISTO ===')
