import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read bot 86
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[86]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# Find the exact line
for i, line in enumerate(code.split('\n')):
    if 'No encontr' in line:
        print(f'L{i+1}: {repr(line)}')
        # Extract the exact text
        l = line.strip()
        # Find the pattern and replace
        old = l
        indent = '        '
        text_expr = 'f"\\ud83d\\uded1 No encontr\\u00e9 ning\\u00fan cliente con la identificaci\\u00f3n num\\u00e9rica: *{cedula_numerica}*. Por favor, verifica el n\\u00famero o escribe *\\"ASESOR\\"*."'
        
        new = f"""{indent}conv = mess_id.conversation_id
{indent}msg_data = {{'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': {text_expr}}}
{indent}back = conv.status
{indent}if back == 'current':
{indent}    conv.send_message_bus_release(msg_data, 'current', False)
{indent}else:
{indent}    conv.block_conversation()
{indent}    conv.send_message_bus_release(msg_data, 'done')
{indent}ret = env['acrux.chat.bot']"""
        
        code = code.replace(line, new)
        print("Replaced!")
        break

# Verify
try:
    compile(code, '<string>', 'exec')
    print("✅ Compiles OK")
except SyntaxError as e:
    print(f"❌ Syntax error L{e.lineno}: {e.msg}")

# Write
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[86], {'code': code}], 'kwargs': {}
    }
})
if resp2.json().get('result'):
    print("✅ Bot 86 written successfully")
else:
    print("❌ Bot 86 write failed")
