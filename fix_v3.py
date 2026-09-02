import requests, json

def call(session, model, method, args=None, kwargs=None):
    if kwargs is None:
        kwargs = {}
    resp = session.post('https://latinbien.com/web/dataset/call_kw/' + model + '/' + method, json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs}
    })
    return resp.json()

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# =========================================================
# 1. MODIFICAR VALIDAR_CEDULA (ID=62) - Atrapar "6"
# =========================================================

old_code = (
    "texto = (mess_id.text or '').strip()\n"
    "if texto:\n"
    "    texto_u = texto.upper().replace(' ', '')\n"
    "    cedula = texto_u\n"
    "    if cedula.startswith('V') or cedula.startswith('E'):\n"
    "        cedula = cedula[1:]\n"
    "    cedula_v = 'V' + cedula\n"
    "    \n"
    "    partner = env['res.partner'].search([('vat', '=', cedula_v)], limit=1)\n"
    "    if not partner:\n"
    "        partner = env['res.partner'].search([('vat', '=', cedula)], limit=1)\n"
    "    \n"
    "    if partner:\n"
    "        p = partner[0]\n"
    "        nombre = p.name or 'cliente'\n"
    "        \n"
    "        linea_activa = False\n"
    "        try:\n"
    "            linea_activa = bool(p.x_activacion_linea)\n"
    "        except:\n"
    "            pass\n"
    "        \n"
    "        tiene_ventas = False\n"
    "        try:\n"
    "            tiene_ventas = bool(p.sale_order_count and p.sale_order_count > 0)\n"
    "        except:\n"
    "            pass\n"
    "        \n"
    "        monto_disp = 0\n"
    "        try:\n"
    "            monto_disp = p.x_credit_limit_available or 0\n"
    "        except:\n"
    "            try:\n"
    "                monto_disp = (p.x_credit_limit_aprobado or 0) - (p.x_credit_limit_use or 0)\n"
    "            except:\n"
    "                pass\n"
    "        \n"
    "        if linea_activa and tiene_ventas:\n"
    "            msg_credito = '\\n\\nTienes un l\\u00edmite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para seguir comprando.'\n"
    "            msg = 'Hola ' + nombre + ', \\u00a1veo que eres parte activa de nuestra comunidad!' + msg_credito + '\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Comprar a cr\\u00e9dito\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "            ret = [{'goto_and_wait': '#MENU_RECOMPRA', 'send_text': msg}]\n"
    "        elif linea_activa and not tiene_ventas:\n"
    "            msg_credito = '\\n\\nTienes un l\\u00edmite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para estrenar.'\n"
    "            msg = 'Hola ' + nombre + ', \\u00a1cuentas con L\\u00ednea de Cr\\u00e9dito activa!' + msg_credito + '\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Comprar a cr\\u00e9dito\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "            ret = [{'goto_and_wait': '#MENU_LC_APROBADA', 'send_text': msg}]\n"
    "        else:\n"
    "            msg = 'Hola ' + nombre + ', est\\u00e1s registrado pero sin L\\u00ednea de Cr\\u00e9dito activa.\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Solicitar mi LC\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "            ret = [{'goto_and_wait': '#No tienes linea', 'send_text': msg}]\n"
    "    else:\n"
    "        msg = 'No encontr\\u00e9 tu c\\u00e9dula. \\u00bfEres nuevo?\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Registrarme y solicitar LC\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Reportar problema\\n5\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "        ret = [{'goto_and_wait': '#Registro', 'send_text': msg}]"
)

new_code = (
    "texto = (mess_id.text or '').strip()\n"
    "if texto == '6':\n"
    "    ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\\\")', 'goto_and_wait': '#BUSCAR_PRODUCTO'}]\n"
    "elif texto:\n"
    "    texto_u = texto.upper().replace(' ', '')\n"
    "    cedula = texto_u\n"
    "    if cedula.startswith('V') or cedula.startswith('E'):\n"
    "        cedula = cedula[1:]\n"
    "    cedula_v = 'V' + cedula\n"
    "    \n"
    "    partner = env['res.partner'].search([('vat', '=', cedula_v)], limit=1)\n"
    "    if not partner:\n"
    "        partner = env['res.partner'].search([('vat', '=', cedula)], limit=1)\n"
    "    \n"
    "    if partner:\n"
    "        p = partner[0]\n"
    "        nombre = p.name or 'cliente'\n"
    "        \n"
    "        linea_activa = False\n"
    "        try:\n"
    "            linea_activa = bool(p.x_activacion_linea)\n"
    "        except:\n"
    "            pass\n"
    "        \n"
    "        tiene_ventas = False\n"
    "        try:\n"
    "            tiene_ventas = bool(p.sale_order_count and p.sale_order_count > 0)\n"
    "        except:\n"
    "            pass\n"
    "        \n"
    "        monto_disp = 0\n"
    "        try:\n"
    "            monto_disp = p.x_credit_limit_available or 0\n"
    "        except:\n"
    "            try:\n"
    "                monto_disp = (p.x_credit_limit_aprobado or 0) - (p.x_credit_limit_use or 0)\n"
    "            except:\n"
    "                pass\n"
    "        \n"
    "        if linea_activa and tiene_ventas:\n"
    "            msg_credito = '\\n\\nTienes un l\\u00edmite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para seguir comprando.'\n"
    "            msg = 'Hola ' + nombre + ', \\u00a1veo que eres parte activa de nuestra comunidad!' + msg_credito + '\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Comprar a cr\\u00e9dito\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "            ret = [{'goto_and_wait': '#MENU_RECOMPRA', 'send_text': msg}]\n"
    "        elif linea_activa and not tiene_ventas:\n"
    "            msg_credito = '\\n\\nTienes un l\\u00edmite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para estrenar.'\n"
    "            msg = 'Hola ' + nombre + ', \\u00a1cuentas con L\\u00ednea de Cr\\u00e9dito activa!' + msg_credito + '\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Comprar a cr\\u00e9dito\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "            ret = [{'goto_and_wait': '#MENU_LC_APROBADA', 'send_text': msg}]\n"
    "        else:\n"
    "            msg = 'Hola ' + nombre + ', est\\u00e1s registrado pero sin L\\u00ednea de Cr\\u00e9dito activa.\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Solicitar mi LC\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "            ret = [{'goto_and_wait': '#No tienes linea', 'send_text': msg}]\n"
    "    else:\n"
    "        msg = 'No encontr\\u00e9 tu c\\u00e9dula. \\u00bfEres nuevo?\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Registrarme y solicitar LC\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Reportar problema\\n5\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "        ret = [{'goto_and_wait': '#Registro', 'send_text': msg}]"
)

print('Modificando VALIDAR_CEDULA...')
resp = call(session, 'acrux.chat.bot', 'write', [[62], {'code': new_code}])
if resp.get('result'):
    print('  OK')
else:
    print('  ERROR:', resp.get('error', {}).get('message', '?'))
    # Maybe the code is too long or has syntax errors
    # Try to verify the code
    print('  Checking new code syntax...')
    # Write code to temp file and check syntax
    with open('C:\\Users\\yarleyc\\AppData\\Local\\Temp\\check_code.py', 'w') as f:
        f.write(new_code)
    import subprocess
    r = subprocess.run(['python', '-c', 'compile(open(r"C:\\Users\\yarleyc\\AppData\\Local\\Temp\\check_code.py").read(), "<test>", "exec")'], capture_output=True, text=True)
    if r.returncode != 0:
        print('  SYNTAX ERROR:', r.stderr)

# =========================================================
# 2. MODIFICAR BUSCAR_PRODUCTO (ID=101) - Volver a CATCHER
# =========================================================

print('\nModificando BUSCAR_PRODUCTO...')
buscar_code = (
    "\n"
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
    "        msg = 'No encontre productos con \\\"' + query + '\\\".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/'\n"
    "except Exception as e:\n"
    "    msg = 'Error al buscar: ' + str(e)\n"
    "\n"
    "ret = [{'send_text': msg, 'goto_and_wait': '#CATCHER CHATBOT (CONECTOR DE COMERCIAL)'}]\n"
)

resp = call(session, 'acrux.chat.bot', 'write', [[101], {'code': buscar_code}])
if resp.get('result'):
    print('  OK')
else:
    print('  ERROR:', resp.get('error', {}).get('message', '?'))

# =========================================================
# 3. VERIFICAR RESULTADO
# =========================================================

print('\n--- RESULTADO FINAL ---')
resp = call(session, 'acrux.chat.bot', 'search_read',
    [[['parent_id', '=', 61]]],
    {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': 'sequence asc'}
)
print('\nHijos de CATCHER:')
for b in resp.get('result', []):
    tm = 'handler' if b['text_match'] == False else repr(b['text_match'])
    print(f'  seq={b["sequence"]} ID={b["id"]} text_match={tm} {b["name"]}')

print('\n--- LISTO ---')
print('Ahora cuando el usuario escriba "6" en CATCHER:')
print('1. VALIDAR_CEDULA ataja el "6"')
print('2. Redirige a BUSCAR_PRODUCTO')
print('3. BUSCAR_PRODUCTO busca el producto y muestra 30% + 20 cuotas')
print('4. Vuelve a CATCHER automaticamente')
