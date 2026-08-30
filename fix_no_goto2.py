import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def write_bot(bot_id, code):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bot_id], {'code': code}], 'kwargs': {}}
    })
    return resp.json()

# Build code using \n literals so the generated code has actual \n escape sequences
# The code that safe_eval sees will have \n which creates newlines in the runtime string

def make_buscar_code(menu_text_items):
    """
    menu_text_items: list of strings like ['1. Comprar a Credito', '2. Comprar de Contado', ...]
    Returns a Python code string safe for safe_eval
    """
    # Build the menu part as code with \n sequences
    menu_code_lines = []
    for item in menu_text_items:
        if menu_code_lines:
            menu_code_lines.append("        + '\\n'")
        menu_code_lines.append("        + " + repr(item))
    
    menu_code = '\\n'.join(menu_text_items)
    # Build the full code string
    code = (
        'try:\n'
        '    query = mess_id.text.strip()\n'
        "    Product = env['product.template']\n"
        "    products = Product.search([('name', 'ilike', '%' + query + '%')], limit=3)\n"
        '    if products:\n'
        "        lines = ['Resultados para: ' + query + '\\n']\n"
        '        for p in products:\n'
        '            precio = p.list_price\n'
        '            if precio and precio > 0:\n'
        '                inicial = round(precio * 0.30, 2)\n'
        '                cuota = round((precio - inicial) / 20, 2)\n'
        '                lines.append(p.name)\n'
        "                lines.append('Precio: $' + '{:.2f}'.format(precio))\n"
        "                lines.append('Inicial (30%): $' + '{:.2f}'.format(inicial))\n"
        "                lines.append('20 cuotas de: $' + '{:.2f}'.format(cuota))\n"
        "                lines.append('')\n"
        '            else:\n'
        "                lines.append(p.name + ' - Consultar precio en tienda')\n"
        "                lines.append('')\n"
        "        lines.append('Catalogo: https://latinbien.com/shop/')\n"
        "        msg = '\\n'.join(lines)\n"
        '    else:\n'
        '        msg = ' + repr('No encontre productos con "' + '".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/') + '\n'
        'except Exception as e:\n'
        '    msg = "Error al buscar: " + str(e)\n'
        '\n'
        # Use built string with \n
        'ret = [{"send_text": msg + "\\n\\n' + menu_code + '"}]'
    )
    return code

# --- MENU DEFINITIONS ---
# Each menu as a list of items (will be joined with \n in the generated code)
MENUS = {
    'RECOMPRA': ['1. Comprar a Credito', '2. Comprar de Contado', '3. Ver Catalogo',
                 '4. Convenio Corporativo', '5. Reportar Problema', '6. Consultar precio de un producto.'],
    'LC':       ['1. Comprar a Credito', '2. Comprar de Contado', '3. Ver Catalogo',
                 '4. Convenio Corporativo', '5. Reportar Problema', '6. Consultar precio de un producto.'],
    'REG':      ['1. Comprar a Credito', '2. Comprar de Contado', '3. Ver Catalogo',
                 '4. Convenio Corporativo', '5. Reportar Problema', '6. Consultar precio de un producto.'],
    'NR':       ['1. Registrarme (llenar formulario)', '2. Ver Catalogo', '3. Hablar con Asesor',
                 '4. Reportar Problema', '5. Comprar a Credito', '6. Consultar precio de un producto.'],
}

BOTS = {
    'BUSCAR_EN_RECOMPRA': 122,
    'BUSCAR_EN_LC':       123,
    'BUSCAR_EN_REG':      124,
    'BUSCAR_EN_NR':       125,
}

for name, bid in BOTS.items():
    suffix = name.split('_')[-1]  # RECOMPRA, LC, REG, NR
    menu_items = MENUS[suffix]
    code = make_buscar_code(menu_items)
    
    resp = write_bot(bid, code)
    ok = resp.get('result')
    print('{} (ID={}): {}'.format(name, bid, 'OK' if ok else 'FAIL'))
    if not ok:
        err = resp.get('error', {})
        print('  ERROR:', err.get('data', {}).get('message', str(err)))
