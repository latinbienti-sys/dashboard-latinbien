import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read prices with and without pricelist context for both products
for pid in [1129, 2464]:
    print(f'--- Product ID={pid} ---')
    for ctx in [None, {'pricelist': 14}]:
        payload = {
            'jsonrpc': '2.0', 'method': 'call',
            'params': {
                'model': 'product.template', 'method': 'read',
                'args': [[pid]],
                'kwargs': {
                    'fields': ['id', 'name', 'list_price', 'price', 'x_precio_final_n8n']
                }
            }
        }
        if ctx:
            payload['params']['kwargs']['context'] = ctx
        
        resp = s.post('https://latinbien.com/web/dataset/call_kw/product.template/read', json=payload)
        r = resp.json()['result'][0]
        print(f'  Context pricelist=14: list_price={r["list_price"]}, price={r.get("price")}, x_precio_final_n8n={r.get("x_precio_final_n8n")}')
