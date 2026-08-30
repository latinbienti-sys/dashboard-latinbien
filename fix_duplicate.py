import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Read bot 62 code
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# Find and replace the duplicated block
# Old duplicated block (lines 30-38):
old_dup = '''                precio = 0
                if p.product_pricelist_ids:
                    precio = p.product_pricelist_ids[0].product_price
                if not precio or precio <= 1.0:
                    precio = 0
                if p.product_pricelist_ids:
                    precio = p.product_pricelist_ids[0].product_price
                if not precio or precio <= 1.0:
                    precio = p.x_precio_final_n8n or p.list_price'''

# New corrected block:
new_single = '''                precio = 0
                if p.product_pricelist_ids:
                    precio = p.product_pricelist_ids[0].product_price
                if not precio or precio <= 1.0:
                    precio = p.x_precio_final_n8n or p.list_price'''

if old_dup in code:
    new_code = code.replace(old_dup, new_single, 1)
    try:
        compile(new_code, '<string>', 'exec')
        print('Syntax OK')
    except SyntaxError as e:
        print(f'Syntax error: {e}')
        exit()
    
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - Bot 62 fixed')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('Duplicated block not found')
    # Show what's at lines 30-38
    lines = code.split('\n')
    for i in range(29, 39):
        print(f'{i+1}: {lines[i]}')
