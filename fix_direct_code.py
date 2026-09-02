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

# Poner el codigo de busqueda DIRECTAMENTE en BUSCAR_PRODUCTO (ID=101)
print('Actualizando BUSCAR_PRODUCTO con codigo de busqueda...')

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
print('OK' if resp.get('result') else 'FAIL: ' + str(resp.get('error', {}).get('message', '')))

# Verify
resp = call(session, 'acrux.chat.bot', 'read', [[101]], {'fields': ['id', 'name', 'text_match', 'code']})
b = resp['result'][0]
print('\nBUSCAR_PRODUCTO:')
tm = repr(b['text_match'])
print(f'  text_match={tm}')
code_preview = b['code'].split('\n')[:10]
for i, line in enumerate(code_preview):
    print(f'  {i+1}: {line}')

print('\n--- PRUEBA ---')
print('1. Escribe "6" desde el menu')
print('2. Escribe "televisor"')
print('BUSCAR_PRODUCTO (handler) procesa directamente la busqueda')
print('Despues de mostrar resultados, vuelve a CATCHER')
