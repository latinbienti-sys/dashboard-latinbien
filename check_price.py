import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Search for iPhone 14
resp = s.post('https://latinbien.com/web/dataset/call_kw/product.template/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'search_read',
        'args': [[('website_published', '=', True), ('name', 'ilike', '%iPhone 14%')]],
        'kwargs': {'fields': ['id', 'name', 'list_price'], 'limit': 10}
    }
})

import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

print('Products found:', len(resp.json()['result']))
for p in resp.json()['result']:
    precio = p['list_price']
    inicial = round(precio * 0.30, 2)
    cuota = round((precio - inicial) / 20, 2)
    print(f'ID={p["id"]}: {p["name"]}')
    print(f'  Precio: ${precio:,.2f}')
    print(f'  Inicial (30%): ${inicial:,.2f}')
    print(f'  20 cuotas de: ${cuota:,.2f}')
    print()
