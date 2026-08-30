import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Hacer BUSCAR_PRODUCTO handler
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {
        'model': 'acrux.chat.bot',
        'method': 'write',
        'args': [[101], {'text_match': False, 'body_whatsapp': False, 'code': ''}],
        'kwargs': {}
    }
})
print('BUSCAR_PRODUCTO -> handler:', resp.json().get('result'))

# Verify
resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {
        'model': 'acrux.chat.bot',
        'method': 'read',
        'args': [[101]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'body_whatsapp']}
    }
})
b = resp2.json()['result'][0]
print(f'  text_match={repr(b["text_match"])}, body_whatsapp={repr(b["body_whatsapp"])}')
