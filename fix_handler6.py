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

# 1. Eliminar CONSULTA_CATCHER (112)
call('acrux.chat.bot', 'unlink', [[112]])
print('CONSULTA_CATCHER eliminado')

# 2. Crear un handler (text_match=False) con seq=1 que verifica si el mensaje es "6"
# Si es "6", muestra el prompt de producto
# Si NO es "6", retorna vacio para que VALIDAR_CEDULA lo procese
HANDLER_6_CODE = """
if mess_id.text.strip() == '6':
    ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\")', 'goto_and_wait': '#BUSCAR_PRODUCTO'}]
else:
    ret = []
"""

resp = call('acrux.chat.bot', 'create', [{
    'name': 'HANDLER_OPCION6',
    'parent_id': 61,  # bajo CATCHER
    'text_match': False,  # handler
    'sequence': 1,  # primero
    'code': HANDLER_6_CODE,
    'body_whatsapp': False,
    'active': True,
}])
hid = resp.get('result')
print(f'HANDLER_OPCION6 creado (ID={hid}) sequence=1')

# 3. Forzar sequence=1
call('acrux.chat.bot', 'write', [[hid], {'sequence': 1}])

# 4. Actualizar BUSCAR_PRODUCTO (101) para que retorne simple
BUSCAR_CODE = """
try:
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
        msg = 'No encontre productos con \\\"' + query + '\\\".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/'
except Exception as e:
    msg = 'Error al buscar: ' + str(e)

ret = [{'send_text': msg}]
"""

call('acrux.chat.bot', 'write', [[101], {'code': BUSCAR_CODE}])
print('BUSCAR_PRODUCTO actualizado (sin goto_and_wait)')

# Verificar orden
print('\n=== Orden final ===')
resp = call('acrux.chat.bot', 'search_read', [[['parent_id', '=', 61]]],
    {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': [['sequence', 'asc']]})
if resp and resp.get('result'):
    for b in resp['result']:
        tm = 'handler' if b['text_match'] == False else 'text_match=' + repr(b['text_match'])
        print(f'  seq={b["sequence"]} ID={b["id"]} {tm} {b["name"]}')

print('\n=== IMPORTANTE ===')
print('El HANDLER_OPCION6 procesa TODO mensaje primero.')
print('Si el mensaje es exactamente "6" -> muestra prompt de producto.')
print('Si NO es "6" -> retorna vacio y VALIDAR_CEDULA lo procesa normalmente.')
print('')
print('Prueba: escribe "6" (sin cedula primero)')
