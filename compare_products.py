import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Compare both products
for pid in [1129, 2464]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/product.template/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'product.template', 'method': 'read',
            'args': [[pid]],
            'kwargs': {'fields': ['id', 'name', 'list_price', 'x_precio_final_n8n', 'x_preciobasecatalogo', 'x_costo_real_calculado']}
        }
    })
    p = resp.json()['result'][0]
    print(p['name'] + ':')
    print('  list_price:', p['list_price'])
    print('  x_precio_final_n8n:', p['x_precio_final_n8n'])
    print('  x_preciobasecatalogo:', p['x_preciobasecatalogo'])
    print('  x_costo_real_calculado:', p['x_costo_real_calculado'])
    fn8n = p.get('x_precio_final_n8n') or 0
    if fn8n:
        print('  / 1.12 =', round(fn8n / 1.12, 2))
    print()
