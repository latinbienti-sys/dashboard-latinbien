import requests, json
session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Compare all sub-bots of MENU_RECOMPRA (body_whatsapp and code)
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['id', 'in', [68, 69, 67, 85, 70]]]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'body_whatsapp', 'code']}
    }
})
for b in resp.json().get('result', []):
    print(f'[{b["id"]}] {b["name"]} (text_match={b["text_match"]})')
    print(f'  body_whatsapp={repr(b.get("body_whatsapp"))}')
    print(f'  code={repr(b.get("code"))}')
    print()
