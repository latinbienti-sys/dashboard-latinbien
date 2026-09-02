import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Helper: map #NAME to bot ID
BOT_MAP = {
    '#MENU_RECOMPRA': 65,
    '#MENU_LC_APROBADA': 66,
    '#MENU_REGISTRADO': 64,
    '#CATCHER': 61,
}

# Read bot 62 original code
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
r = resp.json()
if 'result' in r and r['result']:
    code62 = r['result'][0].get('code', '')
else:
    print('Error reading bot 62')
    exit()

print(f'Original code: {len(code62)} chars, {len(code62.split(chr(10)))} lines')
print()

# The approach: For each ret = [...] pattern, wrap it so that:
# 1. Messages are sent via send_message_bus_release
# 2. Navigation is done via active_bot_id
# 3. ret is set to empty recordset to prevent crash

# Since the original code is very complex, I'll rewrite it completely
# preserving all the logic but changing how messages are sent

new_code = """texto = (mess_id.text or '').strip()
conv = mess_id.conversation_id
Bot = env['acrux.chat.bot']
safe_ret = Bot

def send(txt, goto=None, clear=False):
    msg = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': txt}
    if clear:
        conv.write({'active_bot_id': False})
    elif goto:
        target = Bot.search([('name', '=', goto)], limit=1)
        if target:
            conv.write({'active_bot_id': target.id})
    back = conv.status
    if back == 'current':
        conv.send_message_bus_release(msg, 'current', False)
    else:
        conv.block_conversation()
        conv.send_message_bus_release(msg, 'done')

# ========== MENU OPTIONS (1-6) ==========
if texto == '6':
    send('Escribe 6 seguido del nombre del producto, ej: 6 televisor')

elif texto == '1':
    send('Excelente decision! Registrate y solicita tu Linea de Credito:\\n\\nhttps://latinbien.com/registro')

elif texto == '2':
    send('Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop')

elif texto == '3':
    send('Compra de contado en nuestro catalogo online:\\n\\nhttps://latinbien.com/shop')

elif texto == '4':
    send('Perfecto! He recopilado toda tu informacion con exito. Para garantizarte una asesoria completamente personalizada, te estoy transfiriendo en este instante con uno de nuestros asesores.', clear=True)

elif texto == '5':
    send('Perfecto! He recopilado toda tu informacion con exito. Para garantizarte una asesoria completamente personalizada, te estoy transfiriendo en este instante con uno de nuestros asesores.', clear=True)

elif len(texto) > 2 and texto[0:1] == '6' and texto[1:2] == ' ':
    query = texto[2:].strip()
    if query:
        Product = env['product.template']
        products = Product.search([('website_published', '=', True), ('name', 'ilike', '%' + query + '%')], limit=5)
        if products:
            lines = ['Resultados para: ' + query + '\\n']
            for p in products:
                precio = 0
                if p.product_pricelist_ids:
                    precio = p.product_pricelist_ids[0].product_price
                if not precio or precio <= 1.0:
                    precio = p.x_precio_final_n8n or p.list_price
                if precio and precio > 1.0:
                    factor = 1.378
                    num_cuotas = 20
                    precio_total = round(precio * factor, 2)
                    inicial = round(precio * 0.30, 2)
                    cuota = round((precio_total - inicial) / num_cuotas, 2)
                    lines.append(p.name)
                    lines.append('Precio de contado: $' + '{:,.2f}'.format(precio))
                    lines.append('Valor de Inicial ($): $' + '{:,.2f}'.format(inicial))
                    lines.append('Monto a Financiar ($): $' + '{:,.2f}'.format(cuota * num_cuotas))
                    lines.append('Valor de la Cuota ($): $' + '{:,.2f}'.format(cuota))
                    lines.append('Precio Final a Credito: $' + '{:,.2f}'.format(precio_total))
                    lines.append('')
            if len(lines) > 1:
                lines.append('Catalogo: https://latinbien.com/shop/')
                msg = '\\n'.join(lines)
            else:
                msg = 'No tenemos "' + query + '" disponible en este momento, pero podemos cotizarlo para ti.\\nEscribe COTIZAR y un asesor te contactara.'
        else:
            msg = 'No tenemos "' + query + '" disponible en este momento, pero podemos cotizarlo para ti.\\nEscribe COTIZAR y un asesor te contactara.'
        menu = '\\n\\nEscribe el numero de la opcion deseada:\\n1. Registrarme y solicitar LC\\n2. Ver catalogo\\n3. Compra de contado\\n4. Reportar problema\\n5. Hablar con Asesor\\n6. Consultar precio (escribe 6 + nombre)'
        send(msg + menu)
    else:
        send('Escribe 6 seguido del nombre del producto, ej: 6 nevera')

# ========== CEDULA VALIDATION ==========
elif texto:
    texto_u = texto.upper().replace(' ', '')
    if texto_u.startswith('V') or texto_u.startswith('E'):
        digit_part = texto_u[1:]
        parece_cedula = digit_part.isdigit() and len(digit_part) >= 5
    else:
        parece_cedula = texto_u.isdigit() and len(texto_u) >= 5
    
    if not parece_cedula:
        send('Disculpa, no entendi tu solicitud. Por favor escribe el numero de la opcion deseada o escribe tu numero de cedula para identificarte.')
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
                msg_credito = '\\n\\nTienes un limite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para seguir comprando.'
                msg = 'Hola ' + nombre + ', !veo que eres parte activa de nuestra comunidad!' + msg_credito + '\\n\\nEscribe el numero de la opcion deseada:\\n1\\u20e3 Comprar a credito\\n2\\u20e3 Ver catalogo\\n3\\u20e3 Compra de contado\\n4\\u20e3 Convenio Corporativo\\n5\\u20e3 Reportar problema\\n6\\u20e3 Consultar precio (escribe 6 + nombre)'
                send(msg, goto='MENU_RECOMPRA')
            elif linea_activa and not tiene_ventas:
                msg_credito = '\\n\\nTienes un limite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para estrenar.'
                msg = 'Hola ' + nombre + ', !cuentas con Linea de Credito activa!' + msg_credito + '\\n\\nEscribe el numero de la opcion deseada:\\n1\\u20e3 Comprar a credito\\n2\\u20e3 Ver catalogo\\n3\\u20e3 Compra de contado\\n4\\u20e3 Convenio Corporativo\\n5\\u20e3 Reportar problema\\n6\\u20e3 Consultar precio (escribe 6 + nombre)'
                send(msg, goto='MENU_LC_APROBADA')
            else:
                msg = 'Hola ' + nombre + ', estas registrado pero sin Linea de Credito activa.\\n\\nEscribe el numero de la opcion deseada:\\n1\\u20e3 Solicitar mi LC\\n2\\u20e3 Ver catalogo\\n3\\u20e3 Compra de contado\\n4\\u20e3 Convenio Corporativo\\n5\\u20e3 Reportar problema\\n6\\u20e3 Consultar precio (escribe 6 + nombre)'
                send(msg, goto='MENU_REGISTRADO')
        else:
            msg = 'No encontre tu cedula. Eres nuevo?\\n\\nEscribe el numero de la opcion deseada:\\n1\\u20e3 Registrarme y solicitar LC\\n2\\u20e3 Ver catalogo\\n3\\u20e3 Compra de contado\\n4\\u20e3 Reportar problema\\n5\\u20e3 Hablar con Asesor\\n6\\u20e3 Consultar precio (escribe 6 + nombre)'
            send(msg)

ret = safe_ret"""

# Verify syntax
try:
    compile(new_code, '<string>', 'exec')
    print('Syntax OK')
    print(f'New code: {len(new_code)} chars, {len(new_code.split(chr(10)))} lines')
except SyntaxError as e:
    print(f'Syntax error at line {e.lineno}: {e.msg}')
    print(f'  {e.text}')
    exit()

# Write to bot 62
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[62], {'code': new_code}], 'kwargs': {}
    }
})
if resp2.json().get('result'):
    print('\\u2705 Bot 62 (VALIDAR_CEDULA) actualizado sin ret = [...]')
else:
    print('\\u274c Error:', resp2.json().get('error', {}).get('message','')[:200])
