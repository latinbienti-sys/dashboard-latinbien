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

# 1. Eliminar los bots de prueba
print('Eliminando bots de prueba...')
for bid in [110, 111]:
    call('acrux.chat.bot', 'unlink', [[bid]])
    print(f'  Eliminado bot {bid}')

# 2. Crear un bot CONSULTA_CATCHER bajo CATCHER con sequence=1 (ANTES de VALIDAR_CEDULA)
# Este bot ataja el texto "6" a nivel de CATCHER antes que VALIDAR_CEDULA
CODIGO_CONSULTA_CATCHER = (
    "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\")', 'goto_and_wait': '#BUSCAR_PRODUCTO'}]"
)

resp = call('acrux.chat.bot', 'create', [{
    'name': 'CONSULTA_CATCHER',
    'parent_id': 61,  # bajo CATCHER
    'text_match': '6',
    'sequence': 1,  # ANTES que VALIDAR_CEDULA (seq=7)
    'code': CODIGO_CONSULTA_CATCHER,
    'body_whatsapp': False,
    'active': True,
}])
cid = resp.get('result')
print(f'CONSULTA_CATCHER creado (ID={cid}) sequence=1 text_match="6"')

# 3. Actualizar BUSCAR_PRODUCTO (101) para que retorne al menu correcto
# En lugar de leer el note, vamos a usar un enfoque mas simple:
# BUSCAR_PRODUCTO procesa y retorna al menu RECOMPRA por defecto
CODIGO_BUSCAR_NUEVO = """
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
        msg = 'No encontre productos con "' + query + '".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/'
except Exception as e:
    msg = 'Error al buscar: ' + str(e)

ret = [{'send_text': msg, 'goto_and_wait': '#MENU_RECOMPRA'}]
"""

resp = call('acrux.chat.bot', 'write', [[101], {'code': CODIGO_BUSCAR_NUEVO}])
print(f'BUSCAR_PRODUCTO (101) actualizado -> retorna a #MENU_RECOMPRA')

# 4. Desactivar los bots CONSULTA y BUSCAR bajo los menus (ya no son necesarios)
# Dejamos RECOMPRA_CONSULTA(102) y RECOMPRA_BUSCAR(106) inactivos
for bid in [102, 103, 104, 105, 106, 107, 108, 109]:
    call('acrux.chat.bot', 'write', [[bid], {'active': False}])
    print(f'  Bot {bid} desactivado')

# Verificacion
print('\n=== Hijos de CATCHER por sequence ===')
resp = call('acrux.chat.bot', 'search_read', [[['parent_id', '=', 61]]],
    {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': [['sequence', 'asc']]})
for b in resp.get('result', []):
    print(f'  seq={b["sequence"]} ID={b["id"]} text_match={repr(b["text_match"])} {b["name"]}')

print('\n=== LISTO ===')
print('Ahora cuando el usuario escriba "6" a CUALQUIER nivel:')
print('  1. CONSULTA_CATCHER (seq=1, antes que VALIDAR_CEDULA con seq=7) lo ataja')
print('  2. Muestra: "Escribe el nombre del producto..."')
print('  3. goto_and_wait a BUSCAR_PRODUCTO')
print('  4. Usuario escribe el producto')
print('  5. BUSCAR_PRODUCTO busca y muestra resultados')
print('  6. Retorna a MENU_RECOMPRA')
