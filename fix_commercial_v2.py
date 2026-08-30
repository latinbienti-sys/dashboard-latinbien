# -*- coding: utf-8 -*-
# FIX MAESTRO CONECTOR 2 (COMERCIAL)
# 1. Bot 62 (VALIDAR_CEDULA) -> validación completa + navegacion ret/goto_and_wait
# 2. Reemplazo en bloque mess_id.conversation_id -> mess_id.contact_id (bots conector 2)
# 3. Reescribir bots que usan active_bot_id (campo inexistente)
import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
r = s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
if not r.json().get('result'):
    print('❌ AUTH FAILED'); sys.exit(1)
print('✅ Autenticado')

API = 'https://latinbien.com/web/dataset/call_kw'

def call(model, method, args, kwargs=None):
    resp = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return resp.json().get('result')

# ============================================================
# PASO 1: NUEVO CODIGO BOT 62 (VALIDAR_CEDULA)
# ============================================================
code62 = """texto = (mess_id.text or '').strip()
texto_u = texto.upper().replace(' ', '')

if texto_u.startswith('V') or texto_u.startswith('E'):
    digit_part = texto_u[1:]
    parece_cedula = digit_part.isdigit() and len(digit_part) >= 5
else:
    parece_cedula = texto_u.isdigit() and len(texto_u) >= 5

if not parece_cedula:
    ret = [{'send_text': 'Disculpa, no entendi tu solicitud. Por favor escribe tu numero de cedula para identificarte.', 'exit': True}]
else:
    cedula = texto_u
    if cedula.startswith('V') or cedula.startswith('E'):
        cedula = cedula[1:]
    cedula_v = 'V' + cedula

    partner = env['res.partner'].search([('vat', '=', cedula_v)], limit=1)
    if not partner:
        partner = env['res.partner'].search([('vat', '=', cedula)], limit=1)

    if partner:
        p = partner[0]
        nombre = p.name or 'cliente'

        linea_activa = False
        try:
            linea_activa = bool(p.x_activacion_linea)
        except:
            pass

        tiene_ventas = False
        try:
            tiene_ventas = bool(p.sale_order_count and p.sale_order_count > 0)
        except:
            pass

        monto_disp = 0
        try:
            monto_disp = p.x_credit_limit_available or 0
        except:
            try:
                monto_disp = (p.x_credit_limit_aprobado or 0) - (p.x_credit_limit_use or 0)
            except:
                pass

        if linea_activa and tiene_ventas:
            msg = 'Hola ' + nombre + ', \u00a1veo que eres parte activa de nuestra comunidad!\\n\\nTienes un limite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para seguir comprando.\\n\\nEscribe el numero de la opcion deseada:\\n1\\ufe0f\\u20e3 Comprar a credito\\n2\\ufe0f\\u20e3 Ver catalogo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'
            ret = [{'send_text': msg, 'goto_and_wait': '#MENU_RECOMPRA'}]
        elif linea_activa and not tiene_ventas:
            msg = 'Hola ' + nombre + ', \u00a1cuentas con Linea de Credito activa!\\n\\nTienes un limite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para estrenar.\\n\\nEscribe el numero de la opcion deseada:\\n1\\ufe0f\\u20e3 Comprar a credito\\n2\\ufe0f\\u20e3 Ver catalogo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'
            ret = [{'send_text': msg, 'goto_and_wait': '#MENU_LC_APROBADA'}]
        else:
            msg = 'Hola ' + nombre + ', estas registrado pero sin Linea de Credito activa.\\n\\nEscribe el numero de la opcion deseada:\\n1\\ufe0f\\u20e3 Solicitar mi LC\\n2\\ufe0f\\u20e3 Ver catalogo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'
            ret = [{'send_text': msg, 'goto_and_wait': '#No tienes linea'}]
    else:
        msg = 'No encontre tu cedula. Eres nuevo?\\n\\nEscribe el numero de la opcion deseada:\\n1\\ufe0f\\u20e3 Registrarme y solicitar LC\\n2\\ufe0f\\u20e3 Ver catalogo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Reportar problema\\n5\\ufe0f\\u20e3 Hablar con Asesor\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'
        ret = [{'send_text': msg, 'goto_and_wait': '#Registro'}]"""

# ============================================================
# PASO 3: NUEVOS CODIGOS para bots con active_bot_id
# ============================================================
# Bot 58 ACCESOS: body_whatsapp envia el mensaje; sin navegacion extra
code58 = """ret = env['acrux.chat.bot']"""

# Bot 83 NR_PROBLEMA: quitar active_bot_id
code83 = """conv = mess_id.contact_id
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Perfecto! He recopilado toda tu informacion con exito. Para garantizarte una asesoria completamente personalizada, te estoy transfiriendo en este instante con uno de nuestros asesores.'}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""

# Bot 94 REG_CONTADO: quitar navegacion a 109 (target equivocado)
code94 = """conv = mess_id.contact_id
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Compra de contado en nuestro catalogo online:\\n\\nhttps://latinbien.com/shop'}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""

# Bots CONSULTA (102,103,104,105): navegar al buscador con goto_and_wait
code102 = """ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32")', 'goto_and_wait': '#RECOMPRA_BUSCAR'}]"""
code103 = """ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32")', 'goto_and_wait': '#LC_BUSCAR'}]"""
code104 = """ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32")', 'goto_and_wait': '#REG_BUSCAR'}]"""
code105 = """ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32")', 'goto_and_wait': '#NR_BUSCAR'}]"""

# Bots BUSCAR (107,108,109): patron igual al bot 106 que funciona
code107 = """try:
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
        lines.append('Catalogo: https://latinbien.com/shop/')
        msg = '\\n'.join(lines)
    else:
        msg = 'No encontre productos con "' + query + '".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/'
except Exception as e:
    msg = 'Error al buscar: ' + str(e)

ret = [{'send_text': msg, 'goto_and_wait': '#MENU_LC_APROBADA'}]"""

code108 = code107.replace("'#MENU_LC_APROBADA'", "'#No tienes linea'")
code109 = code107.replace("'#MENU_LC_APROBADA'", "'#Registro'")

# Bot 117 PROCESAR_BUSQUEDA: volver al catcher
code117 = """try:
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
        lines.append('Catalogo: https://latinbien.com/shop/')
        msg = '\\n'.join(lines)
    else:
        msg = 'No encontre productos con "' + query + '".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/'
except Exception as e:
    msg = 'Error al buscar: ' + str(e)

ret = [{'send_text': msg, 'goto_and_wait': '#COMERCIAL'}]"""

# Bot 101 BUSCAR_PRODUCTO: quitar texto de prueba
code101 = """conv = mess_id.contact_id
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Escribe el nombre del producto que deseas buscar (ej: nevera, televisor)'}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""

# Bot 86 EVALUAR CEDULA CONVENIO: reescritura completa (usa mess_id.text y ret)
code86 = """try:
    p_rec = None
    cedula_ingresada = ""
    try:
        if mess_id.text:
            cedula_ingresada = str(mess_id.text).strip().replace(" ", "").upper()
    except:
        pass
    cedula_numerica = "".join([c for c in cedula_ingresada if c.isdigit()])
    if cedula_numerica:
        p_rec = env['res.partner'].search(['|', ('vat', 'ilike', cedula_numerica), ('vat', 'ilike', cedula_ingresada)], limit=1)
        if not p_rec:
            p_rec = env['res.partner'].search([('name', 'ilike', cedula_numerica)], limit=1)
    if p_rec:
        cliente = p_rec[0]
        nombre_cliente = cliente.name
        es_miembro_convenio = False
        try:
            if cliente.x_tipo_de_solicitante == 'B':
                es_miembro_convenio = True
        except:
            pass
        empresa_convenio = None
        try:
            empresa_convenio = cliente.x_convenio_afiliado
        except:
            pass
        if es_miembro_convenio and empresa_convenio:
            nombre_empresa = empresa_convenio.name
            msg_convenio = '\\u00a1Qu\\u00e9 gran beneficio, *' + nombre_cliente + '*! \\ud83d\\ude0a Puedes disfrutar de nuestro convenio activo con *' + nombre_empresa + '*.\\n\\nPara conocer tus beneficios exclusivos y recibir asesor\\u00eda personalizada, escribe la palabra *"ASESOR"*.'
            ret = [{'send_text': msg_convenio}]
        else:
            linea_activa = False
            try:
                linea_activa = cliente.x_activacion_linea
            except:
                pass
            tiene_ventas = False
            try:
                tiene_ventas = cliente.sale_order_count > 0
            except:
                pass
            credito_usado = False
            try:
                credito_usado = cliente.x_credit_limit_use > 0
            except:
                pass
            texto_base_no_conv = 'Hola *' + nombre_cliente + '*. En mi sistema no se encuentra registrado que pertenezcas a alguno de nuestros convenios activos. Pero a\\u00fan hay un mill\\u00f3n de oportunidades en Latinbien para ti. \\ud83d\\ude0a\\n\\nPor favor, elige una opci\\u00f3n enviando el n\\u00famero correspondiente para ayudarte:\\n\\n'
            if linea_activa and not (tiene_ventas or credito_usado):
                msg_no_conv = texto_base_no_conv + '1\\ufe0f\\u20e3 \\ud83d\\uded2 Comprar un producto a cr\\u00e9dito (Usar mi l\\u00ednea disponible)\\n2\\ufe0f\\u20e3 \\ud83d\\udcb0 Realizar una compra de contado\\n3\\ufe0f\\u20e3 \\ud83d\\udcd6 Ver el cat\\u00e1logo online y precios de productos\\n5\\ufe0f\\u20e3 \\u26a0\\ufe0f Reportar un problema'
                ret = [{'send_text': msg_no_conv, 'goto_and_wait': '#MENU_RECOMPRA'}]
            else:
                msg_no_conv = texto_base_no_conv + '1\\ufe0f\\u20e3 \\ud83d\\udcdd Registrarme y solicitar mi L\\u00ednea de Cr\\u00e9dito por primera vez\\n2\\ufe0f\\u20e3 \\ud83d\\udcd6 Ver el cat\\u00e1logo online y precios de productos\\n3\\ufe0f\\u20e3 \\ud83d\\udcb0 Realizar una compra de contado\\n4\\ufe0f\\u20e3 \\u26a0\\ufe0f Reportar un problema'
                ret = [{'send_text': msg_no_conv, 'goto_and_wait': '#Registro'}]
    else:
        ret = [{'send_text': '\\ud83d\\uded1 No encontr\\u00e9 ning\\u00fan cliente con la identificaci\\u00f3n num\\u00e9rica: *' + cedula_numerica + '*. Por favor, verifica el n\\u00famero o escribe *"ASESOR"*.'}]
except Exception as e:
    ret = [{'send_text': '\\ud83d\\uded1 *Error al validar convenio:* ' + str(e)}]"""

# ============================================================
# APLICAR
# ============================================================
def safe_compile(name, code):
    try:
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError as ex:
        print(f'   ❌ SYNTAX ERROR {name}: {ex}')
        return False

print('\n=== PASO 1: Bot 62 (VALIDAR_CEDULA) ===')
if safe_compile('62', code62):
    res = call('acrux.chat.bot', 'write', [[62], {'code': code62}])
    print(f'   ✅ Bot 62 escrito: {res}')

print('\n=== PASO 2: Reemplazo en bloque conversation_id -> contact_id (conector 2) ===')
bots = call('acrux.chat.bot', 'search_read', [[('connector_id', '=', 2)]], {'fields': ['id', 'name', 'code']})
fixed = 0
for b in bots:
    if not b.get('code'):
        continue
    if 'conversation_id' in b['code']:
        new_code = b['code'].replace('mess_id.conversation_id', 'mess_id.contact_id')
        if safe_compile(str(b['id']), new_code):
            res = call('acrux.chat.bot', 'write', [[b['id']], {'code': new_code}])
            if res:
                fixed += 1
                print(f"   ✅ Bot {b['id']} ({b['name'][:35]}): conversation_id -> contact_id")
            else:
                print(f"   ❌ Bot {b['id']}: write fallo")
print(f'   Total reemplazados: {fixed}')

print('\n=== PASO 3: Bots con active_bot_id (reescritura) ===')
targets = [
    (58, code58, 'ACCESOS'),
    (83, code83, 'NR_PROBLEMA'),
    (94, code94, 'REG_CONTADO'),
    (101, code101, 'BUSCAR_PRODUCTO'),
    (102, code102, 'RECOMPRA_CONSULTA'),
    (103, code103, 'LC_CONSULTA'),
    (104, code104, 'REG_CONSULTA'),
    (105, code105, 'NR_CONSULTA'),
    (107, code107, 'LC_BUSCAR'),
    (108, code108, 'REG_BUSCAR'),
    (109, code109, 'NR_BUSCAR'),
    (117, code117, 'PROCESAR_BUSQUEDA'),
    (86, code86, 'EVALUAR CEDULA CONVENIO'),
]
for bid, code, name in targets:
    if safe_compile(str(bid), code):
        res = call('acrux.chat.bot', 'write', [[bid], {'code': code}])
        print(f"   ✅ Bot {bid} ({name}): {'OK' if res else 'FALLO'}")

print('\n=== VERIFICACION FINAL: buscar conversation_id / active_bot_id restantes en conector 2 ===')
bots = call('acrux.chat.bot', 'search_read', [[('connector_id', '=', 2)]], {'fields': ['id', 'name', 'code']})
pend = [b for b in bots if b.get('code') and ('conversation_id' in b['code'] or 'active_bot_id' in b['code'])]
if pend:
    for b in pend:
        print(f"   ⚠️  Bot {b['id']} ({b['name'][:40]}) aun tiene conversation_id/active_bot_id")
else:
    print('   ✅ Ningun bot del conector 2 usa campos inexistentes')
