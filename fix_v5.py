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
# ENFOQUE NUEVO: 
# - Crear bot BUSCAR_PRECIO como bot "normal" (no handler, no text_match)
# - Su body_whatsapp muestra el prompt
# - Su hijo handler busca el producto
# - VALIDAR_CEDULA redirige con send_text + goto_and_wait
# =========================================================

# 1. ACTUALIZAR BUSCAR_PRODUCTO (ID=101) - text_match no vacio
print('1. Actualizando BUSCAR_PRODUCTO...')
body = 'Escribe el nombre del producto que deseas consultar (ej: televisor 32 pulgadas)'
resp = call(session, 'acrux.chat.bot', 'write', [[101], {
    'text_match': 'PROMPT_BUSQUEDA',  # string NO vacio -> NO es handler
    'body_whatsapp': body,
    'code': ''
}])
print('  OK' if resp.get('result') else '  FAIL: ' + str(resp.get('error',{}).get('message','')))

# 2. Verify PROCESAR_BUSQUEDA child exists
resp = call(session, 'acrux.chat.bot', 'search_read',
    [[['parent_id', '=', 101]]],
    {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': 'sequence asc'}
)
print('\n2. Hijos de BUSCAR_PRODUCTO:')
for b in resp.get('result', []):
    tm = 'handler' if b['text_match'] == False else repr(b['text_match'])
    print(f'  seq={b["sequence"]} ID={b["id"]} text_match={tm} {b["name"]}')

# 3. Update VALIDAR_CEDULA to send_text + goto_and_wait
print('\n3. Actualizando VALIDAR_CEDULA...')
new_code = (
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
    "            ret = [{'goto_and_wait': '#No tienes linea', 'send_text': msg}]\n"
    "    else:\n"
    "        msg = 'No encontr\\u00e9 tu c\\u00e9dula. \\u00bfEres nuevo?\\n\\nElige una opci\\u00f3n:\\n1\\ufe0f\\u20e3 Registrarme y solicitar LC\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Reportar problema\\n5\\ufe0f\\u20e3 Consultar precio de producto'\n"
    "        ret = [{'goto_and_wait': '#Registro', 'send_text': msg}]"
)

resp = call(session, 'acrux.chat.bot', 'write', [[62], {'code': new_code}])
print('  OK' if resp.get('result') else '  FAIL: ' + str(resp.get('error',{}).get('message','')))

# Verificar estructura completa
print('\n4. Verificando...')
resp = call(session, 'acrux.chat.bot', 'search_read',
    [[['parent_id', '=', 61]]],
    {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': 'sequence asc'}
)
print('Hijos de CATCHER:')
for b in resp.get('result', []):
    if b['text_match'] == False:
        tm = 'handler'
    elif b['text_match'] == '' or b['text_match'] is None:
        tm = 'EMPTY'
    else:
        tm = repr(b['text_match'])
    print(f'  seq={b["sequence"]} ID={b["id"]} text_match={tm} {b["name"]}')

print('\n--- PRUEBA ---')
print('Escribe "6" en WhatsApp')
print('VALIAR_CEDULA debe enviar el prompt y redirigir a BUSCAR_PRODUCTO')
print('BUSCAR_PRODUCTO NO es handler (text_match=PROMPT_BUSQUEDA)')
print('SU hijo PROCESAR_BUSQUEDA (handler) procesa la busqueda')
