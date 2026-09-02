import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# New code for NOT FOUND (45) - send menu directly without goto_and_wait
new_code = """# Send welcome menu for unrecognized messages
ret = [{'send_text': '\u00a1Hola, bienvenid@ a Latinbien! Soy \ud83e\udd16 LatinBot y ser\u00e9 tu  \ud83d\udc49Asistente Virtual.\\n\\nPor favor elige una opci\u00f3n del men\u00fa enviando al chat el n\u00famero que corresponda:  \\n\\n1\ufe0f\u20e3 Pagar y reportar mi cuota \\n2\ufe0f\u20e3 Ver mi estado de cuenta \\n3\ufe0f\u20e3 Ver los m\u00e9todos de pago\\n4\ufe0f\u20e3 Explorar nuestro cat\u00e1logo\\n5\ufe0f\u20e3 Hablar con un asesor \\n\\n#\ufe0f\u20e3 Salir. \u27a1\ufe0f\\n\\n\u00a1En Latinbien te impulsamos a alcanzar tus metas! \u2728'}]"""

# Verify syntax
try:
    compile(new_code, '<string>', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error: {e}')
    exit()

# Write to bot 45
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[45], {'code': new_code}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print('OK - Bot 45 (NOT FOUND) actualizado con el men\u00fa de cobranza')
else:
    print('ERROR:', resp.json().get('error', {}))

# Read back to verify
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[45]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b45 = resp2.json()['result'][0]
print()
print('C\u00f3digo guardado:')
for i, line in enumerate(b45['code'].split('\n')):
    print(f'  L{i+1}: {line}')
