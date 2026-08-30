import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read the pricelist.product records for both products
resp = s.post('https://latinbien.com/web/dataset/call_kw/pricelist.product/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'pricelist.product', 'method': 'read',
        'args': [[35501, 35502]],
        'kwargs': {'fields': ['id', 'display_name', 'product_tmpl_id', 'pricelist_id', 'price']}
    }
})
print('Pricelist.product records:')
for r in resp.json().get('result', []):
    print(json.dumps(r, indent=2, ensure_ascii=False))
    print()
