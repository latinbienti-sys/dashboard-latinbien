import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Backup current code
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[61]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
backup_code = resp.json()['result'][0]['code']
print(f"Backup saved ({len(backup_code)} chars)")

# Write simplest possible code
test_code = """conv = mess_id.conversation_id
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Hola esto es una prueba del bot comercial'}
conv.send_message_bus_release(msg_data, 'current', False)
ret = env['acrux.chat.bot']"""

try:
    compile(test_code, '<string>', 'exec')
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[61], {'code': test_code}], 'kwargs': {}
        }
    })
    if resp.json().get('result'):
        print("✅ Bot 61: código de prueba instalado")
    else:
        print("❌ Bot 61: error al escribir")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
