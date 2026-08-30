import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def write_code(bot_id, code):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bot_id], {'code': code}], 'kwargs': {}
        }
    })
    return resp.json()

# The NEW complete code for all 4 handlers
# Using r'' raw strings to avoid escaping issues
NEW_CODE_BASE = r"""try:
    query = mess_id.text.strip()
    if query.startswith('6 '):
        query = query[2:].strip()
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
            msg = 'Ese producto no esta disponible en este momento, pero podemos cotizarlo para ti.\nEscribe COTIZAR y un asesor te contactara.'
    else:
        msg = 'No tenemos "' + query + '" disponible en este momento, pero podemos cotizarlo para ti.\nEscribe COTIZAR y un asesor te contactara.'
except Exception as e:
    msg = 'Error al buscar: ' + str(e)

MENU = '\n\n1. Comprar a Credito\n2. Comprar de Contado\n3. Ver Catalogo\n4. Convenio Corporativo\n5. Reportar Problema\n6. Consultar precio de un producto.'
ret = [{'send_text': msg + MENU}]"""

# Same code but with NR menu for bot 125
NEW_CODE_NR = r"""try:
    query = mess_id.text.strip()
    if query.startswith('6 '):
        query = query[2:].strip()
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
            msg = 'Ese producto no esta disponible en este momento, pero podemos cotizarlo para ti.\nEscribe COTIZAR y un asesor te contactara.'
    else:
        msg = 'No tenemos "' + query + '" disponible en este momento, pero podemos cotizarlo para ti.\nEscribe COTIZAR y un asesor te contactara.'
except Exception as e:
    msg = 'Error al buscar: ' + str(e)

MENU = '\n\n1. Registrarme (llenar formulario)\n2. Ver Catalogo\n3. Hablar con Asesor\n4. Reportar Problema\n5. Comprar a Credito\n6. Consultar precio de un producto.'
ret = [{'send_text': msg + MENU}]"""

bots = [
    (122, 'BUSCAR_EN_RECOMPRA', NEW_CODE_BASE),
    (123, 'BUSCAR_EN_LC', NEW_CODE_BASE),
    (124, 'BUSCAR_EN_REG', NEW_CODE_BASE),
    (125, 'BUSCAR_EN_NR', NEW_CODE_NR),
]

for bot_id, name, new_code in bots:
    result = write_code(bot_id, new_code)
    if result.get('result'):
        print('{} (ID={}): OK'.format(name, bot_id))
    else:
        print('{} (ID={}): FAIL - {}'.format(name, bot_id, result.get('error', {})))
