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
# 1. RESTAURAR VALIDAR_CEDULA (ID=62) - version produccion con "6"
# =========================================================
print('1. Restaurando VALIDAR_CEDULA...')
prod_code = (
    "texto = (mess_id.text or '').strip()\n"
    "if texto == '6':\n"
    "    ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32 pulgadas)', 'goto_and_wait': '#BUSCAR_PRODUCTO'}]\n"
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
    "            ret = [{'goto_and_wait': '#MENU_REGISTRADO', 'send_text': msg}]\n"
    "    else:\n"
    "        msg = 'No encontr\\u00e9 tu c\\u00e9dula. \\u00bfEres nuevo?\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Registrarme y solicitar LC\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Reportar problema\\n5\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "        ret = [{'goto_and_wait': '#MENU_NO_REGISTRADO', 'send_text': msg}]"
)

resp = call(session, 'acrux.chat.bot', 'write', [[62], {'code': prod_code}])
print('  OK' if resp.get('result') else '  FAIL: ' + str(resp.get('error',{}).get('message','')))

# =========================================================
# 2. AGREGAR "6" a cada menu (text_match="6" child -> BUSCAR_PRODUCTO)
# =========================================================
menus = [
    (65, 'MENU_RECOMPRA'),
    (66, 'MENU_LC_APROBADA'),
    (64, 'MENU_REGISTRADO'),
    (63, 'MENU_NO_REGISTRADO'),
]

option6_code = "ret = [{'goto_and_wait': '#BUSCAR_PRODUCTO'}]"

for menu_id, menu_name in menus:
    # Check if already has a "6" child
    existing = call(session, 'acrux.chat.bot', 'search_read',
        [[['parent_id', '=', menu_id], ['text_match', '=', '6']]],
        {'fields': ['id']}
    )
    if existing.get('result') and len(existing['result']) > 0:
        ex_id = existing['result'][0]['id']
        print(f'2. {menu_name} (ID={menu_id}): ya tiene hijo "6" (ID={ex_id})')
        continue
    
    resp = call(session, 'acrux.chat.bot', 'create', [{
        'name': 'CONSULTA_PRECIO_6',
        'parent_id': menu_id,
        'text_match': '6',
        'sequence': 99,  # after all other options
        'code': option6_code,
        'body_whatsapp': False,
        'active': True,
    }])
    new_id = resp.get('result')
    if new_id:
        print(f'2. {menu_name} (ID={menu_id}): hijo "6" creado (ID={new_id})')
    else:
        err_msg = resp.get('error', {}).get('message', '?')
        print(f'2. {menu_name} (ID={menu_id}): ERROR - {err_msg}')

# =========================================================
# 3. VERIFICAR
# =========================================================
print('\n3. Verificando menus...')
for menu_id, menu_name in menus:
    resp = call(session, 'acrux.chat.bot', 'search_read',
        [[['parent_id', '=', menu_id]]],
        {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': 'sequence asc'}
    )
    kids = resp.get('result', [])
    matching_6 = [k for k in kids if k['text_match'] == '6']
    if matching_6:
        m_id = matching_6[0]['id']
        m_seq = matching_6[0]['sequence']
        print(f'  {menu_name}: TIENE opcion 6 (ID={m_id}, seq={m_seq})')
    else:
        print(f'  {menu_name}: NO tiene opcion 6')

print('\n--- LISTO ---')
print('Ahora escribe "6" desde cualquier menu y deberia redirigir a BUSCAR_PRODUCTO')
print('(BUSCAR_PRODUCTO tiene body_whatsapp con el prompt)')
print('(PROCESAR_BUSQUEDA hijo busca el producto)')
