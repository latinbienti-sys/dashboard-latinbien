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

# ---------------------------------------------------------------------------
# 1. Crear BUSCAR_PRODUCTO (handler, bot_key='#BUSCAR_PRODUCTO')
# ---------------------------------------------------------------------------
CODIGO_BUSCAR = """
try:
    conv = mess_id.contact_id
    note = conv.note or ''
    menu_key = '#MENU_RECOMPRA'
    if 'return_menu=' in note:
        menu_key = note.split('return_menu=')[1].strip().split('\\n')[0]
    
    query = mess_id.text.strip()
    Product = env['product.template']
    products = Product.search([('name', 'ilike', '%' + query + '%')], limit=3)
    
    if products:
        lines = ['Resultados para: ' + query + '\\n']
        for p in products:
            precio = p.list_price
            if precio and precio > 0:
                inicial = round(precio * 0.30, 2)
                cuota = round((precio - inicial) / 20, 2)
                lines.append(p.name)
                lines.append('Precio: $' + '{:.2f}'.format(precio))
                lines.append('Inicial (30%): $' + '{:.2f}'.format(inicial))
                lines.append('20 cuotas de: $' + '{:.2f}'.format(cuota))
                lines.append('')
            else:
                lines.append(p.name + ' - Consultar precio en tienda')
                lines.append('')
        lines.append('Catalogo completo: https://latinbien.com/shop/')
        msg = '\\n'.join(lines)
    else:
        msg = 'No encontre productos con "' + query + '".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/'
except Exception as e:
    msg = 'Error al buscar el producto: ' + str(e)

conv.write({'note': False})
ret = [{'send_text': msg}, {'goto_and_wait': menu_key}]
"""

print('Creando BUSCAR_PRODUCTO...')
resp = call('acrux.chat.bot', 'create', [{
    'name': 'BUSCAR_PRODUCTO',
    'parent_id': 61,  # bajo CATCHER
    'text_match': False,
    'bot_key': '#BUSCAR_PRODUCTO',
    'code': CODIGO_BUSCAR,
    'body_whatsapp': False,
    'active': True,
}])
buscar_id = resp.get('result')
if buscar_id:
    print(f'  BUSCAR_PRODUCTO creado (ID={buscar_id})')
else:
    print(f'  ERROR: {resp.get("error",{}).get("message","???")}')
    exit()

# ---------------------------------------------------------------------------
# 2. Crear bots CONSULTA bajo cada menu
# ---------------------------------------------------------------------------
# Codigo para los bots CONSULTA (cada uno con su return_menu hardcodeado)
def make_consulta_code(return_menu):
    # Escape properly for JSON
    return (
        "conv = mess_id.contact_id\\n"
        "conv.write({'note': 'return_menu=" + return_menu + "'})\\n"
        "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\\\")'}, {'goto_and_wait': '#BUSCAR_PRODUCTO'}]"
    )

# Escapar para JSON: las \\n deben ser \\\\n en el string Python que se envia
# En Python: "line1\\nline2" -> cuando se escribe en JSON, se convierte a "line1\\nline2"
# En Odoo se almacena como line1\nline2 (literal backslash-n)
# Al evaluarlo, se interpreta como newline

def escape_code_for_json(code_text):
    """Take a Python multi-line string and prepare it for JSON storage"""
    # Replace real newlines with literal \\n for storage
    return code_text.replace('\\n', '\\\\n').replace('"', '\\"')

CONSULTA_BOTS = [
    {'parent_id': 65, 'name': 'RECOMPRA_CONSULTA', 'text_match': '6', 'return_menu': '#MENU_RECOMPRA'},
    {'parent_id': 66, 'name': 'LC_CONSULTA', 'text_match': '6', 'return_menu': '#MENU_LC_APROBADA'},
    {'parent_id': 64, 'name': 'REG_CONSULTA', 'text_match': '6', 'return_menu': '#No tienes linea'},
    {'parent_id': 63, 'name': 'NR_CONSULTA', 'text_match': '5', 'return_menu': '#Registro'},
]

print('\nCreando bots CONSULTA...')
for bot in CONSULTA_BOTS:
    code = (
        "conv = mess_id.contact_id\n"
        "conv.write({'note': 'return_menu=" + bot['return_menu'] + "'})\n"
        "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\\\")'}, {'goto_and_wait': '#BUSCAR_PRODUCTO'}]"
    )
    # Para guardar en Odoo, necesitamos \\n en lugar de newlines reales
    # porque lo vamos a enviar como JSON y Odoo lo almacena literal
    stored_code = code.replace('\\n', '\\\\n')
    
    resp = call('acrux.chat.bot', 'create', [{
        'name': bot['name'],
        'parent_id': bot['parent_id'],
        'text_match': bot['text_match'],
        'code': stored_code,
        'body_whatsapp': False,
        'active': True,
    }])
    cid = resp.get('result')
    if cid:
        print(f'  {bot["name"]} (ID={cid}) text_match={bot["text_match"]}')
    else:
        print(f'  ERROR {bot["name"]}: {resp.get("error",{}).get("message","???")}')

# ---------------------------------------------------------------------------
# 3. Actualizar body_whatsapp de los menus
# ---------------------------------------------------------------------------
MENU_TEXTOS = {
    65: (
        "Cu\u00e9ntame, \u00bfqu\u00e9 te gustar\u00eda hacer hoy? Elige una opci\u00f3n enviando el n\u00famero correspondiente:\n\n"
        "1\ufe0f\u20e3 \ud83d\uded2 Comprar un producto a cr\u00e9dito (Usar mi l\u00ednea disponible)\n"
        "2\ufe0f\u20e3 \ud83d\udcb0 Realizar una compra de contado\n"
        "3\ufe0f\u20e3 \ud83d\udcd6 Ver el cat\u00e1logo online y precios de productos\n"
        "4\ufe0f\u20e3 \ud83e\udd1d Verificar si pertenezco a un Convenio Corporativo\n"
        "5\ufe0f\u20e3 \u26a0\ufe0f Reportar un problema\n"
        "6\ufe0f\u20e3 \ud83d\udd0d Consultar precio de un producto"
    ),
    66: (
        "Cu\u00e9ntame, \u00bfqu\u00e9 te gustar\u00eda hacer hoy? Elige una opci\u00f3n enviando el n\u00famero correspondiente:\n\n"
        "1\ufe0f\u20e3 \ud83d\uded2 Comprar un producto a cr\u00e9dito (Usar mi l\u00ednea disponible)\n"
        "2\ufe0f\u20e3 \ud83d\udcb0 Realizar una compra de contado\n"
        "3\ufe0f\u20e3 \ud83d\udcd6 Ver el cat\u00e1logo online y precios de productos\n"
        "4\ufe0f\u20e3 \ud83e\udd1d Verificar si pertenezco a un Convenio Corporativo\n"
        "5\ufe0f\u20e3 \u26a0\ufe0f Reportar un problema\n"
        "6\ufe0f\u20e3 \ud83d\udd0d Consultar precio de un producto"
    ),
    64: (
        "Elige una opci\u00f3n que desees consultar enviando *solo* el n\u00famero correspondiente para ayudarte:\n\n"
        "1\ufe0f\u20e3 \ud83d\ude80 \u00a1Quiero solicitar mi L\u00ednea de Cr\u00e9dito ya!\n"
        "2\ufe0f\u20e3 \ud83d\udcd6 Ver el cat\u00e1logo online y precios de productos\n"
        "3\ufe0f\u20e3 \ud83d\udcb0 Realizar una compra de contado\n"
        "4\ufe0f\u20e3 \ud83e\udd1d Verificar si pertenezco a un Convenio Corporativo\n"
        "5\ufe0f\u20e3 \u26a0\ufe0f Reportar un problema\n"
        "6\ufe0f\u20e3 \ud83d\udd0d Consultar precio de un producto"
    ),
    63: (
        "Por favor, selecciona una opci\u00f3n del men\u00fa para ayudarte. Env\u00edanos el n\u00famero de la opci\u00f3n que desees:\n\n"
        "1\ufe0f\u20e3 \ud83d\udcdd Registrarme y solicitar mi L\u00ednea de Cr\u00e9dito por primera vez\n"
        "2\ufe0f\u20e3 \ud83d\udcd6 Ver el cat\u00e1logo online y precios de productos\n"
        "3\ufe0f\u20e3 \ud83d\udcb0 Realizar una compra de contado\n"
        "4\ufe0f\u20e3 \u26a0\ufe0f Reportar un problema\n"
        "5\ufe0f\u20e3 \ud83d\udd0d Consultar precio de un producto"
    ),
}

print('\nActualizando body_whatsapp de menus...')
for bid, cuerpo in MENU_TEXTOS.items():
    resp = call('acrux.chat.bot', 'write', [[bid], {'body_whatsapp': cuerpo}])
    if resp.get('result'):
        print(f'  Menu {bid} -> OK')
    else:
        print(f'  Menu {bid} -> ERROR: {resp.get("error",{}).get("message","???")}')

# ---------------------------------------------------------------------------
# 4. Verificacion final
# ---------------------------------------------------------------------------
print('\n=== VERIFICACION FINAL ===')
resp = call('acrux.chat.bot', 'search_read', [[['id', 'in', [buscar_id]]]], 
    {'fields': ['id', 'name', 'bot_key', 'text_match', 'parent_id']})
for b in resp.get('result', []):
    pid = b.get('parent_id', ['',''])
    print(f'  {b["id"]} {b["name"]} bot_key={b.get("bot_key")} text_match={b.get("text_match")} parent={pid[1] if isinstance(pid, list) else pid}')

# Listar los nuevos CONSULTA
resp = call('acrux.chat.bot', 'search_read', [[['name', 'like', '%CONSULTA%']]],
    {'fields': ['id', 'name', 'text_match', 'parent_id']})
for b in resp.get('result', []):
    pid = b.get('parent_id', ['',''])
    print(f'  {b["id"]} {b["name"]} text_match={b.get("text_match")} parent={pid[1] if isinstance(pid, list) else pid}')

print('\n=== LISTO ===')
