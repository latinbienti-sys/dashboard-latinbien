import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Update all 5 bots: replace base price calculation
# Old: precio = p.x_precio_final_n8n or p.list_price
# New: precio = (p.x_precio_final_n8n or p.list_price) / 1.12

bots = [62, 122, 123, 124, 125]
for bid in bots:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    r = resp.json()['result'][0]
    c = r['code']
    
    # Check which pattern exists
    if 'x_precio_final_n8n or p.list_price' in c:
        old = 'precio = p.x_precio_final_n8n or p.list_price'
        new = 'precio = (p.x_precio_final_n8n or p.list_price) / 1.12'
        new_c = c.replace(old, new, 1)
        
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
            print(f'OK - {r["name"]} (ID={bid}) updated: / 1.12')
        else:
            print(f'ERROR on {r["name"]}:', resp2.json().get('error', {}))
    elif 'precio = p.list_price' in c:
        old = 'precio = p.list_price'
        new = 'precio = p.list_price / 1.12'
        new_c = c.replace(old, new, 1)
        
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
            print(f'OK - {r["name"]} (ID={bid}) updated: / 1.12 (list_price)')
        else:
            print(f'ERROR on {r["name"]}:', resp2.json().get('error', {}))
    else:
        print(f'No match in {r["name"]} (ID={bid})')
