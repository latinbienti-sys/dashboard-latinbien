import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def call(model, method, args, kwargs=None):
    if kwargs is None:
        kwargs = {}
    resp = session.post('https://latinbien.com/web/dataset/call_kw/' + model + '/' + method, json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs}
    })
    return resp.json()

# Verificar VALIDAR_CEDULA code - buscar la seccion de goto_and_wait
resp = call('acrux.chat.bot', 'search_read', [[['id', '=', 62]]], {'fields': ['id', 'code']})
code = resp.get('result', [{}])[0].get('code', '')

# Buscar todas las lineas con goto_and_wait
lines = code.split('\n')
print('=== Lineas con goto_and_wait en VALIDAR_CEDULA ===')
for i, line in enumerate(lines, 1):
    if 'goto_and_wait' in line:
        print(f'  Linea {i}: {line.strip()}')

# Buscar lineas con send_text
print('\n=== Lineas con send_text ===')
for i, line in enumerate(lines, 1):
    if 'send_text' in line and 'menu' in line.lower():
        print(f'  Linea {i}: {line[:200].strip()}')

print('\n=== Ultimas 10 lineas del codigo ===')
for line in lines[-10:]:
    print(f'  {line}')
