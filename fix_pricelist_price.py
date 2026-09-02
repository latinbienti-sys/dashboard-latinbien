import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Old price line patterns (16-space indent for bot 62, 12-space indent for buscar bots)
old_patterns = [
    'precio = p.x_precio_final_n8n or p.list_price',
    'precio = p.list_price',
]

# New price line
new_price = '''precio = 0
                if p.product_pricelist_ids:
                    precio = p.product_pricelist_ids[0].product_price
                if not precio or precio <= 1.0:
                    precio = p.x_precio_final_n8n or p.list_price'''

# Update all 5 bots
for bid in [62, 122, 123, 124, 125]:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    r = resp.json()['result'][0]
    c = r['code']
    
    updated = False
    for old in old_patterns:
        if old in c:
            # The indentation in the code might be different
            # Let's find the exact line and its indentation
            lines = c.split('\n')
            for i, line in enumerate(lines):
                if old in line:
                    indent = line[:len(line) - len(line.lstrip())]
                    # Create new price block with same indentation
                    new_price_indented = indent + ('\n' + indent).join(new_price.split('\n'))
                    lines[i] = new_price_indented
                    break
            c = '\n'.join(lines)
            updated = True
    
    if updated:
        try:
            compile(c, '<string>', 'exec')
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
            print(f'OK - {r["name"]} (ID={bid})')
        else:
            print(f'ERROR on {r["name"]}:', resp2.json().get('error', {}))
    else:
        print(f'No old pattern in {r["name"]} (ID={bid})')
