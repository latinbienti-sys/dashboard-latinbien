import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Original code for bot 62 (restore)
original_code = """texto = (mess_id.text or '').strip()

# ========== MENU OPTIONS (1-6) ==========
if texto == '6':
    ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 televisor'}]

elif texto == '1':
    ret = [{'send_text': 'Excelente decision! Registrate y solicita tu Linea de Credito:\\n\\nhttps://latinbien.com/registro'}]

elif texto == '2':
    ret = [{'send_text': 'Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop'}]

elif texto == '3':
    ret = [{'send_text': 'Compra de contado en nuestro catalogo online:\\n\\nhttps://latinbien.com/shop'}]

elif texto == '4':
    ret = [{'send_text': 'Perfecto! He recopilado toda tu informacion con exito. Para garantizarte una asesoria completamente personalizada, te estoy transfiriendo en este instante con uno de nuestros asesores.'}, {'clear_catcher': True}]

elif texto == '5':
    ret = [{'send_text': 'Perfecto! He recopilado toda tu informacion con exito. Para garantizarte una asesoria completamente personalizada, te estoy transfiriendo en este instante con uno de nuestros asesores.'}, {'clear_catcher': True}]

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
        menu = '\\n\\nEscribe el n\\u00famero de la opci\\u00f3n deseada:\\n1. Registrarme y solicitar LC\\n2. Ver catalogo\\n3. Compra de contado\\n4. Reportar problema\\n5. Hablar con Asesor\\n6. Consultar precio (escribe 6 + nombre)'
        ret = [{'send_text': msg + menu}]
    else:
        ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 nevera'}]

# ========== CEDULA VALIDATION ==========
elif texto:
    texto_u = texto.upper().replace(' ', '')
    # Check if it looks like a valid cedula format
    if texto_u.startswith('V') or texto_u.startswith('E'):
        digit_part = texto_u[1:]
        parece_cedula = digit_part.isdigit() and len(digit_part) >= 5
    else:
        parece_cedula = texto_u.isdigit() and len(texto_u) >= 5
    
    if not parece_cedula:
        ret = [{'send_text': 'Disculpa, no entendi tu solicitud. Por favor escribe el n\\u00famero de la opci\\u00f3n deseada o escribe tu numero de cedula para identificarte.'}]
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
                msg_credito = '\\n\\nTienes un l\\u00edmite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para seguir comprando.'
                msg = 'Hola ' + nombre + ', \\u00a1veo que eres parte activa de nuestra comunidad!' + msg_credito + '\\n\\nEscribe el n\\u00famero de la opci\\u00f3n deseada:\\n1\\ufe0f\\u20e3 Comprar a cr\\u00e9dito\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'
                ret = [{'goto_and_wait': '#MENU_RECOMPRA', 'send_text': msg}]
            elif linea_activa and not tiene_ventas:
                msg_credito = '\\n\\nTienes un l\\u00edmite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para estrenar.'
                msg = 'Hola ' + nombre + ', \\u00a1cuentas con L\\u00ednea de Cr\\u00e9dito activa!' + msg_credito + '\\n\\nEscribe el n\\u00famero de la opci\\u00f3n deseada:\\n1\\ufe0f\\u20e3 Comprar a cr\\u00e9dito\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'
                ret = [{'goto_and_wait': '#MENU_LC_APROBADA', 'send_text': msg}]
            else:
                msg = 'Hola ' + nombre + ', est\\u00e1s registrado pero sin L\\u00ednea de Cr\\u00e9dito activa.\\n\\nEscribe el n\\u00famero de la opci\\u00f3n deseada:\\n1\\ufe0f\\u20e3 Solicitar mi LC\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Convenio Corporativo\\n5\\ufe0f\\u20e3 Reportar problema\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'
                ret = [{'goto_and_wait': '#MENU_REGISTRADO', 'send_text': msg}]
        else:
            msg = 'No encontr\\u00e9 tu c\\u00e9dula. \\u00bfEres nuevo?\\n\\nEscribe el n\\u00famero de la opci\\u00f3n deseada:\\n1\\ufe0f\\u20e3 Registrarme y solicitar LC\\n2\\ufe0f\\u20e3 Ver cat\\u00e1logo\\n3\\ufe0f\\u20e3 Compra de contado\\n4\\ufe0f\\u20e3 Reportar problema\\n5\\ufe0f\\u20e3 Hablar con Asesor\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'
            ret = [{'send_text': msg}]"""

# Verify syntax
try:
    compile(original_code, '<string>', 'exec')
    print('Syntax OK - Original code verified')
except SyntaxError as e:
    print(f'Syntax error at line {e.lineno}: {e.msg}')
    exit()

# Write original code back to bot 62
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[62], {'code': original_code}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print('OK - Bot 62 (COBRANZA) RESTORED to original code')
else:
    print('ERROR:', resp.json().get('error', {}))

# Read back to confirm
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp2.json()['result'][0]['code']
# Check it starts correctly
first_lines = code.split('\n')[:5]
for i, line in enumerate(first_lines):
    print(f'  L{i+1}: {line}')
