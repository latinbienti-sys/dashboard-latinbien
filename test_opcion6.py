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

# 1. Primero, limpiar logs de prueba
print('Limpiando logs...')
resp = call('acrux.chat.bot.log', 'search', [[['id', '>', 0]]])
ids = resp.get('result', [])
if ids:
    call('acrux.chat.bot.log', 'unlink', [ids])
    print(f'  Eliminados {len(ids)} logs')

# 2. Crear bot de prueba bajo CATCHER (61) con text_match='6'
TEST_CODE = "ret = [{'send_text': 'PRUEBA: OPCION 6 FUNCIONA DESDE CATCHER'}, {'goto_and_wait': '#MENU_RECOMPRA'}]"

resp = call('acrux.chat.bot', 'create', [{
    'name': 'TEST_OPCION6_CATCHER',
    'parent_id': 61,  # bajo CATCHER
    'text_match': '6',
    'code': TEST_CODE,
    'body_whatsapp': False,
    'active': True,
}])
test_id = resp.get('result')
if test_id:
    print(f'\nBot TEST_OPCION6_CATCHER (ID={test_id}) creado bajo CATCHER con text_match="6"')

# 3. Tambien crear bajo VALIDAR_CEDULA para probar
resp = call('acrux.chat.bot', 'create', [{
    'name': 'TEST_OPCION6_VALIDAR',
    'parent_id': 62,  # bajo VALIDAR_CEDULA
    'text_match': '6',
    'code': TEST_CODE,
    'body_whatsapp': False,
    'active': True,
}])
test_id2 = resp.get('result')
if test_id2:
    print(f'Bot TEST_OPCION6_VALIDAR (ID={test_id2}) creado bajo VALIDAR_CEDULA con text_match="6"')

# Verificar
resp = call('acrux.chat.bot', 'search_read', [[['name', 'like', 'TEST_%']]],
    {'fields': ['id', 'name', 'text_match', 'parent_id']})
for b in resp.get('result', []):
    pid = b.get('parent_id', ['',''])
    print(f'  {b["id"]} {b["name"]} text_match={b["text_match"]} parent_id={pid[0] if isinstance(pid, list) else pid}')

print('\n=== PRUEBA ===')
print('Ahora escribe tu cedula, espera el menu, y escribe "6"')
print('Si ves "PRUEBA: OPCION 6 FUNCIONA DESDE CATCHER" -> el problema es la navegacion desde VALIDAR_CEDULA')
print('Si ves "PRUEBA: OPCION 6 FUNCIONA DESDE..." -> el problema es el matching bajo MENU_RECOMPRA')
print('Si vuelve a pedir cedula -> revisamos logs')
