import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get full product data for iPhone 14
resp = s.post('https://latinbien.com/web/dataset/call_kw/product.template/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'read',
        'args': [[1129]],
        'kwargs': {'fields': ['id', 'name', 'list_price', 'lst_price', 'standard_price', 'website_price', 'website_published', 'public_categ_ids', 'x_precio_final', 'x_precio_credito', 'x_inicial', 'x_cuotas']}
    }
})
print(json.dumps(resp.json()['result'][0], indent=2, ensure_ascii=False))
