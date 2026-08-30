import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

for bid in [62, 122, 123, 124, 125]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    r = resp.json()['result'][0]
    c = r['code']
    count_pricelist = c.count('product_pricelist_ids')
    count_x_precio = c.count('x_precio_final_n8n or p.list_price')
    dup = 'precio = 0\n' in c and c.count('precio = 0\n') > 1
    status = 'OK' if count_pricelist == 1 and count_x_precio == 1 and not dup else 'ISSUE'
    print(f'{r["name"]} (ID={bid}): pricelist={count_pricelist}, fallback={count_x_precio}, dup={dup} -> {status}')
