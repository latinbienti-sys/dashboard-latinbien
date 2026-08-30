import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# The COMPLETE correct code for VALIDAR_CEDULA (ID=62)
new_code = r"""texto = (mess_id.text or '').strip()

# ========== MENU OPTIONS (1-6) ==========
if texto == '6':
    ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 televisor'}]

elif texto == '1':
    ret = [{'send_text': 'Excelente decision! Registrate y solicita tu Linea de Credito:\n\nhttps://latinbien.com/registro'}]

elif texto == '2':
    ret = [{'send_text': 'Nuestro catalogo online se actualiza constantemente!\n\nExplora nuestros productos: https://latinbien.com/shop'}]

elif texto == '3':
    ret = [{'send_text': 'Compra de contado en nuestro catalogo online:\n\nhttps://latinbien.com/shop'}]

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
            lines = ['Resultados para: ' + query + '\n']
            for p in products:
                precio = p.list_price
                if precio and precio > 1.0:
                    inicial = round(precio * 0.30, 2)
                    cuota = round((precio - inicial) / 20, 2)
                    lines.append(p.name)
                    lines.append('Precio: $' + '{:,.2f}'.format(precio))
                    lines.append('Inicial (30%): $' + '{:,.2f}'.format(inicial))
                    lines.append('20 cuotas de: $' + '{:,.2f}'.format(cuota))
                    lines.append('')
            if len(lines) > 1:
                lines.append('Catalogo: https://latinbien.com/shop/')
                msg = '\n'.join(lines)
            else:
                msg = 'No tenemos "' + query + '" disponible en este momento, pero podemos cotizarlo para ti.\nEscribe COTIZAR y un asesor te contactara.'
        else:
            msg = 'No tenemos "' + query + '" disponible en este momento, pero podemos cotizarlo para ti.\nEscribe COTIZAR y un asesor te contactara.'
        menu = '\n\n1. Registrarme y solicitar LC\n2. Ver catalogo\n3. Compra de contado\n4. Reportar problema\n5. Hablar con Asesor\n6. Consultar precio (escribe 6 + nombre)'
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
        ret = [{'send_text': 'Disculpa, no entendi tu solicitud. Por favor elige una opcion del menu o escribe tu numero de cedula para identificarte.'}]
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
                msg_credito = '\n\nTienes un l\u00edmite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para seguir comprando.'
                msg = 'Hola ' + nombre + ', \u00a1veo que eres parte activa de nuestra comunidad!' + msg_credito + '\n\nElige una opci\u00f3n:\n1\ufe0f\u20e3 Comprar a cr\u00e9dito\n2\ufe0f\u20e3 Ver cat\u00e1logo\n3\ufe0f\u20e3 Compra de contado\n4\ufe0f\u20e3 Convenio Corporativo\n5\ufe0f\u20e3 Reportar problema\n6\ufe0f\u20e3 Consultar precio (escribe 6 + nombre)'
                ret = [{'goto_and_wait': '#MENU_RECOMPRA', 'send_text': msg}]
            elif linea_activa and not tiene_ventas:
                msg_credito = '\n\nTienes un l\u00edmite disponible de $ ' + '{:,.2f}'.format(monto_disp).replace(',', '.') + ' para estrenar.'
                msg = 'Hola ' + nombre + ', \u00a1cuentas con L\u00ednea de Cr\u00e9dito activa!' + msg_credito + '\n\nElige una opci\u00f3n:\n1\ufe0f\u20e3 Comprar a cr\u00e9dito\n2\ufe0f\u20e3 Ver cat\u00e1logo\n3\ufe0f\u20e3 Compra de contado\n4\ufe0f\u20e3 Convenio Corporativo\n5\ufe0f\u20e3 Reportar problema\n6\ufe0f\u20e3 Consultar precio (escribe 6 + nombre)'
                ret = [{'goto_and_wait': '#MENU_LC_APROBADA', 'send_text': msg}]
            else:
                msg = 'Hola ' + nombre + ', est\u00e1s registrado pero sin L\u00ednea de Cr\u00e9dito activa.\n\nElige una opci\u00f3n:\n1\ufe0f\u20e3 Solicitar mi LC\n2\ufe0f\u20e3 Ver cat\u00e1logo\n3\ufe0f\u20e3 Compra de contado\n4\ufe0f\u20e3 Convenio Corporativo\n5\ufe0f\u20e3 Reportar problema\n6\ufe0f\u20e3 Consultar precio (escribe 6 + nombre)'
                ret = [{'goto_and_wait': '#MENU_REGISTRADO', 'send_text': msg}]
        else:
            msg = 'No encontr\u00e9 tu c\u00e9dula. \u00bfEres nuevo?\n\nElige una opci\u00f3n:\n1\ufe0f\u20e3 Registrarme y solicitar LC\n2\ufe0f\u20e3 Ver cat\u00e1logo\n3\ufe0f\u20e3 Compra de contado\n4\ufe0f\u20e3 Reportar problema\n5\ufe0f\u20e3 Hablar con Asesor\n6\ufe0f\u20e3 Consultar precio (escribe 6 + nombre)'
            ret = [{'send_text': msg}]
"""

# Verify syntax
try:
    compile(new_code, '<string>', 'exec')
    print('Syntax check: OK')
except SyntaxError as e:
    print(f'Syntax error: {e}')
    lines = new_code.split('\n')
    for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
        print(f'  {i+1}: {lines[i]}')
    exit()

# Write to bot
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[62], {'code': new_code}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print('OK - VALIDAR_CEDULA code replaced successfully')
else:
    print('ERROR:', resp.json().get('error', {}))
