import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Update bot 62 (VALIDAR_CEDULA) - 16-space indent
old_62 = '                precio = p.x_precio_final_n8n or p.list_price'
new_62 = '''                precio = 0
                if p.product_pricelist_ids:
                    precio = p.product_pricelist_ids[0].product_price
                if not precio or precio <= 1.0:
                    precio = p.x_precio_final_n8n or p.list_price'''

# Update buscar bots (122-125) - 12-space indent
old_12 = '            precio = p.x_precio_final_n8n or p.list_price'
new_12 = '''            precio = 0
            if p.product_pricelist_ids:
                precio = p.product_pricelist_ids[0].product_price
            if not precio or precio <= 1.0:
                precio = p.x_precio_final_n8n or p.list_price'''

updates = [(62, old_62, new_62)]
for bid in [122, 123, 124, 125]:
    updates.append((bid, old_12, new_12))

for bid, old, new in updates:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    r = resp.json()['result'][0]
    c = r['code']
    
    if old in c:
        c = c.replace(old, new, 1)
        try:
            compile(c, '<string>', 'exec')
            print(f'Syntax OK for {r["name"]} (ID={bid})')
        except SyntaxError as e:
            print(f'Syntax error in {r["name"]}: {e}')
            continue
        
        resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[bid], {'code': c}], 'kwargs': {}
            }
        })
        if resp2.json().get('result'):
            print(f'OK - {r["name"]} updated')
        else:
            print(f'ERROR:', resp2.json().get('error', {}))
    else:
        print(f'Old pattern NOT found in {r["name"]} (ID={bid})')
        # Show what's there
        idx = c.find('precio =')
        if idx >= 0:
            print(f'  Found: {repr(c[idx:idx+100])}')
