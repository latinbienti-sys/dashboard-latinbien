import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Ver si existe product.template
resp = session.post('https://latinbien.com/web/dataset/call_kw/product.template/search_count', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'search_count', 'args': [[]], 'kwargs': {}}
})
count = resp.json().get('result', 0)
print(f'Total products in product.template: {count}')

# Ver algunos productos de ejemplo
if count > 0:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/product.template/search_read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'product.template', 'method': 'search_read',
            'args': [[]],
            'kwargs': {'fields': ['id', 'name', 'list_price', 'default_code', 'categ_id'], 'limit': 20}
        }
    })
    prods = resp.json().get('result', [])
    print(f'\nPrimeros {len(prods)} productos:')
    for p in prods:
        cat = p.get('categ_id', ['',''])
        print(f'  {p["id"]}: {p["name"]} - ${p.get("list_price",0)} - cat={cat[1] if isinstance(cat, list) else cat}')
else:
    # Probar product.product
    resp = session.post('https://latinbien.com/web/dataset/call_kw/product.product/search_count', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'product.product', 'method': 'search_count', 'args': [[]], 'kwargs': {}}
    })
    count2 = resp.json().get('result', 0)
    print(f'Total products in product.product: {count2}')
    if count2 > 0:
        resp = session.post('https://latinbien.com/web/dataset/call_kw/product.product/search_read', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'product.product', 'method': 'search_read',
                'args': [[]],
                'kwargs': {'fields': ['id', 'name', 'list_price', 'default_code'], 'limit': 20}
            }
        })
        prods = resp.json().get('result', [])
        print(f'\nPrimeros {len(prods)} productos:')
        for p in prods:
            print(f'  {p["id"]}: {p["name"]} - ${p.get("list_price",0)}')
