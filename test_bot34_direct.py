import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Put simple response directly in bot 34 (CATCHER COBRANZA)
# If even this doesn't work, the issue is the WhatsApp connection, not the bot
simple_code = "ret = [{'send_text': 'Hola, soy LatinBot de Cobranza. Escribe 1, 2, 3, 4, 5 o #'}]"

resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[34], {'code': simple_code}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print('OK - Codigo directo en Bot 34')
else:
    print('ERROR:', resp.json().get('error', {}))

# Verify
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[34]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b34 = resp2.json()['result'][0]
print(f'Bot 34 code: {repr(b34["code"])}')
