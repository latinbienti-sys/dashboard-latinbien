import requests, json, sys

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

result = {}
for bid in [65, 66, 64, 63, 61]:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
            'args': [[['id', '=', bid]]],
            'kwargs': {'fields': ['id', 'name', 'body_whatsapp']}
        }
    })
    bot = resp.json().get('result', [])
    if bot:
        b = bot[0]
        body = b.get('body_whatsapp')
        result[f'{bid}_{b["name"]}'] = {
            'len': len(body) if body else 0,
            'body': body if body else None
        }

# Save to file to avoid encoding issues
with open('c:/users/yarleyc/documents/new opencode project/menus_body.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=True, indent=2)

for key, val in result.items():
    print(f'{key}: len={val["len"]}')
    if val['body']:
        print(f'  first 80 chars: {json.dumps(val["body"][:80], ensure_ascii=True)}')
