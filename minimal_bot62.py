import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Simplest code - just echo received text
code62 = """conv = mess_id.conversation_id
texto = (mess_id.text or '').strip()
m = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Recibido: ' + texto + ' (' + str(len(texto)) + ' chars)'}
conv.send_message_bus_release(m, 'current', False)
ret = env['acrux.chat.bot']"""

try:
    compile(code62, '<string>', 'exec')
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': code62}], 'kwargs': {}
        }
    })
    if resp.json().get('result'):
        print("✅ Bot 62: código MÍNIMO instalado")
    else:
        print("❌ Error")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
