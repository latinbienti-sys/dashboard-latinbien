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

# DEBUG: Hacer que VALIDAR_CEDULA responda a TODO
print('=== DEBUG: VALIDAR_CEDULA va a responder a todo mensaje ===')
debug_code = (
    "texto = (mess_id.text or '').strip()\n"
    "if texto == '6':\n"
    "    ret = [{'send_text': 'DEBUG-6: Recibi el numero 6. texto=' + repr(texto)}]\n"
    "elif texto:\n"
    "    ret = [{'send_text': 'DEBUG-OTRO: Recibi: ' + repr(texto) + ' | len=' + str(len(texto))}]\n"
    "else:\n"
    "    ret = [{'send_text': 'DEBUG-VACIO: mensaje vacio o nulo'}]"
)

resp = call(session, 'acrux.chat.bot', 'write', [[62], {'code': debug_code}])
print('OK' if resp.get('result') else 'FAIL: ' + str(resp.get('error',{}).get('message','')))

# Read back
resp = call(session, 'acrux.chat.bot', 'read', [[62]], {'fields': ['code']})
stored = resp['result'][0]['code']
print('\nCodigo almacenado:')
print(stored)

print('\n--- PRUEBA FINAL ---')
print('1. Escribe "6" en WhatsApp')
print('2. Escribe cualquier otra cosa (ej: "hola")')
print('3. Escribe una cedula valida (ej: V12345678)')
print('')
print('Deberias ver respuestas DEBUG-6, DEBUG-OTRO, etc.')
print('Si NO ves NADA -> VALIDAR_CEDULA no se esta ejecutando')
