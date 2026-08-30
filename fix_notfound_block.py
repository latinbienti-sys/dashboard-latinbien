import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Updated code for Bot 45 - matching exact pattern from Bot 44/47
code45 = """# Send menu for unrecognized messages
conv = mess_id.conversation_id
text = '\\U0001f916 *LatinBot*: Disculpa, no puedo entenderte, por favor *"Escribe en el Chat \\U0001f4e3 SOLO EL NUMERO"* de la opci\\u00f3n que quieras elegir:  \\U0001f449 *1, 2, 3, 4, 5, #* \\U0001f448'
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': text}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')"""

# Verify syntax
try:
    compile(code45, '<string>', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error: {e}')
    exit()

# Write to bot 45
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[45], {'code': code45}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print('OK - Bot 45 actualizado con patr\u00f3n block_conversation()')
else:
    print('ERROR:', resp.json().get('error', {}))

# Verify
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[45]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b45 = resp2.json()['result'][0]
print()
print('C\u00f3digo guardado en Bot 45:')
for i, line in enumerate(b45['code'].split('\n')):
    print(f'  L{i+1}: {line}')
