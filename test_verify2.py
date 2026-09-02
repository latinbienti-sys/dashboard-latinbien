import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

for bid in [102, 106]:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
            'args': [[['id', '=', bid]]],
            'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'bot_key']}
        }
    })
    b = resp.json().get('result', [])
    if b:
        print(f'=== {b[0]["id"]} {b[0]["name"]} ===')
        print(f'text_match={b[0].get("text_match")}  bot_key={b[0].get("bot_key")}')
        print(f'code:\n{b[0]["code"]}')
        print()
