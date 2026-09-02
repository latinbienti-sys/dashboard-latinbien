import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def call(model, method, args=None, kwargs=None):
    if kwargs is None:
        kwargs = {}
    resp = session.post('https://latinbien.com/web/dataset/call_kw/' + model + '/' + method, json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs}
    })
    return resp.json()

# Read current code
resp = call('acrux.chat.bot', 'read', [[62]], {'fields': ['id', 'name', 'code']})
current = resp['result'][0]
code = current['code']

# Build new code: replace the 'if texto == "6": ... goto_and_wait ...' 
# with inline search logic

# The search + menu code to replace the "6" block
new_6_handler = """if texto.startswith('6 '):
    query = texto[2:].strip()
    if query:
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
        menu = '\\n\\n1. Comprar a Credito\\n2. Comprar de Contado\\n3. Ver Catalogo\\n4. Convenio Corporativo\\n5. Reportar Problema\\n6. Consultar precio de un producto.'
        ret = [{'send_text': msg + menu}]
    else:
        ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 televisor'}]
elif texto == '6':
    ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 televisor'}]"""

# Replace the old block in the code
old_block = """if texto == '6':
    ret = [
        {'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32 pulgadas)'},
        {'goto_and_wait': '#BUSCAR_PRODUCTO'}
    ]"""

print("Replacing old block with new inline handler...")
new_code = code.replace(old_block, new_6_handler)

# Verify the replacement happened
if new_code == code:
    print("ERROR: Old block not found! Checking exact match...")
    # Print the actual lines around "if texto"
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if 'if texto' in line:
            print(f"Line {i}: [{repr(line)}]")
else:
    print("OK - replacement successful")

print("\n=== NEW CODE ===")
print(new_code[:500])
print("...")

# Now write it
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[62], {'code': new_code}], 'kwargs': {}}
})
result = resp.json()
if result.get('result'):
    print("\n✅ Write SUCCESS")
else:
    print("\n❌ Write FAILED")
    print(result.get('error', {}))
