import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def call(session, model, method, args=None, kwargs=None):
    if kwargs is None:
        kwargs = {}
    resp = session.post('https://latinbien.com/web/dataset/call_kw/' + model + '/' + method, json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs}
    })
    return resp.json()

# 1. Add code to CATCHER (ID=61) to catch "6"
print('1. Agregando codigo a CATCHER...')
catcher_code = (
    "if (mess_id.text or '').strip() == '6':\n"
    "    ret = [{'send_text': 'PRUEBA DESDE CATCHER - Recibi el 6'}]\n"
)
resp = call(session, 'acrux.chat.bot', 'write', [[61], {'code': catcher_code}])
print('  OK' if resp.get('result') else '  FAIL: ' + str(resp.get('error',{}).get('message','')))

# 2. Read CATCHER to verify
resp = call(session, 'acrux.chat.bot', 'read', [[61]], {'fields': ['id', 'name', 'code']})
catcher_name = resp['result'][0]['name']
catcher_code_str = repr(resp['result'][0]['code'])
print(f'  Codigo CATCHER ({catcher_name}): {catcher_code_str}')

print('\n--- PRUEBA ---')
print('Escribe "6" en WhatsApp')
print('Deberias ver: "PRUEBA DESDE CATCHER - Recibi el 6"')
print('Si ves esto, CATCHER recibe el mensaje pero VALIDAR_CEDULA no lo atrapaba')
print('Si NO ves esto, el problema esta en como llega el mensaje a CATCHER')
