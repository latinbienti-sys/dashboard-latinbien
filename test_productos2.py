import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Buscar productos con "televisor" o "tv" en el nombre
resp = session.post('https://latinbien.com/web/dataset/call_kw/product.template/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'search_read',
        'args': [[['name', 'ilike', '%televisor%']]],
        'kwargs': {'fields': ['id', 'name', 'list_price', 'default_code'], 'limit': 10}
    }
})
print('Productos con "televisor":')
for p in resp.json().get('result', []):
    print(f'  {p["id"]}: {p["name"]} - ${p.get("list_price",0)}')

# Buscar "tv"
resp = session.post('https://latinbien.com/web/dataset/call_kw/product.template/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'search_read',
        'args': [[['name', 'ilike', '%tv%']]],
        'kwargs': {'fields': ['id', 'name', 'list_price', 'default_code'], 'limit': 10}
    }
})
print('\nProductos con "tv":')
for p in resp.json().get('result', []):
    print(f'  {p["id"]}: {p["name"]} - ${p.get("list_price",0)}')

# Buscar "led"
resp = session.post('https://latinbien.com/web/dataset/call_kw/product.template/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'search_read',
        'args': [[['name', 'ilike', '%led%']]],
        'kwargs': {'fields': ['id', 'name', 'list_price', 'default_code'], 'limit': 15}
    }
})
print('\nProductos con "led":')
for p in resp.json().get('result', []):
    print(f'  {p["id"]}: {p["name"]} - ${p.get("list_price",0)}')

# Ver precios para calcular ejemplo
# Supongamos un producto de $200
precio = 200.0
inicial = round(precio * 0.30, 2)
cuota = round((precio - inicial) / 20, 2)
print(f'\n--- Ejemplo calculo para producto de ${precio} ---')
print(f'Inicial (30%): ${inicial}')
print(f'20 cuotas de: ${cuota}')
print(f'Total: ${inicial + cuota * 20}')
