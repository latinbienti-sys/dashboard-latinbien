import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# The OLD calculation block (pattern with /1.12 and interest) - 12-space indent for BUSCAR bots
old_calc_block_12 = """            precio = (p.x_precio_final_n8n or p.list_price) / 1.12
            if precio and precio > 1.0:
                inicial = round(precio * 0.30, 2)
                financiado = precio - inicial
                tasa_interes = 2.70 / 100
                num_cuotas = 20
                precio_total = precio + (financiado * tasa_interes * num_cuotas)
                cuota = round((precio_total - inicial) / num_cuotas, 2)
                lines.append(p.name)
                lines.append('Precio de contado: $' + '{:,.2f}'.format(precio))
                lines.append('Valor de Inicial ($): $' + '{:,.2f}'.format(inicial))
                lines.append('Monto a Financiar ($): $' + '{:,.2f}'.format(cuota * num_cuotas))
                lines.append('Valor de la Cuota ($): $' + '{:,.2f}'.format(cuota))
                lines.append('Precio Final a Credito: $' + '{:,.2f}'.format(precio_total))"""

# New block - 12-space indent
new_calc_block_12 = """            precio = p.x_precio_final_n8n or p.list_price
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
                lines.append('Precio Final a Credito: $' + '{:,.2f}'.format(precio_total))"""

# Update BUSCAR_EN bots (122-125) with 12-space indent
for bid in [122, 123, 124, 125]:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    r = resp.json()['result'][0]
    c = r['code']
    
    if old_calc_block_12 in c:
        new_c = c.replace(old_calc_block_12, new_calc_block_12, 1)
        try:
            compile(new_c, '<string>', 'exec')
        except SyntaxError as e:
            print(f'Syntax error in {r["name"]}: {e}')
            continue
        resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[bid], {'code': new_c}], 'kwargs': {}
            }
        })
        if resp2.json().get('result'):
            print(f'OK - {r["name"]} (ID={bid})')
        else:
            print(f'ERROR on {r["name"]}:', resp2.json().get('error', {}))
    else:
        print(f'Old 12-space block not found in {r["name"]} (ID={bid})')
        idx = c.find('precio =')
        if idx >= 0:
            print(f'  Found: {c[idx:idx+80]}')
