import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Read current code
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# The old calculation block (inside the product search for '6 <query>')
old_calc = """                precio = p.list_price
                if precio and precio > 1.0:
                    inicial = round(precio * 0.30, 2)
                    cuota = round((precio - inicial) / 20, 2)"""

new_calc = """                precio = p.x_precio_final_n8n or p.list_price
                if precio and precio > 1.0:
                    inicial = round(precio * 0.30, 2)
                    financiado = precio - inicial
                    tasa_interes = 2.70 / 100
                    num_cuotas = 20
                    precio_total = precio + (financiado * tasa_interes * num_cuotas)
                    cuota = round((precio_total - inicial) / num_cuotas, 2)"""

if old_calc in code:
    new_code = code.replace(old_calc, new_calc, 1)
    print('Old calculation found and replaced')
else:
    print('Old calculation NOT found')
    # Debug
    idx = code.find('p.list_price')
    if idx >= 0:
        print('p.list_price found at', idx)
        print(code[max(0,idx-20):idx+80])
    else:
        print('p.list_price not found in code')
        # Let's search for 'list_price' 
        for i, line in enumerate(code.split(chr(10)), 1):
            if 'list_price' in line or 'precio' in line:
                print(f'  {i}: {line}')

# Also need to update: 
# The old product search has precio/print format
# Check if 'Precio:' format needs updating to show precio_total vs precio
# Currently: lines.append('Precio: $' + '{:,.2f}'.format(precio))
# Should show the base price AND the final price

# Check syntax
try:
    compile(new_code, '<string>', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error: {e}')
    lines = new_code.split(chr(10))
    for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
        print(f'  {i+1}: {lines[i]}')
    exit()

# Write
resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[62], {'code': new_code}], 'kwargs': {}
    }
})
if resp2.json().get('result'):
    print('OK - Price calculation updated')
else:
    print('ERROR:', resp2.json().get('error', {}))
