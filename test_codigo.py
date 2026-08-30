import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Almacenar resultados en archivo para evitar problemas de encoding
result = {}

for bid in [101, 102, 103, 104, 105]:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
            'args': [[['id', '=', bid]]],
            'kwargs': {'fields': ['id', 'name', 'text_match', 'bot_key', 'code', 'body_whatsapp']}
        }
    })
    bot = resp.json().get('result', [])
    if bot:
        b = bot[0]
        result[str(bid)] = {
            'name': b['name'],
            'text_match': b.get('text_match'),
            'bot_key': b.get('bot_key'),
            'code': b.get('code', ''),
            'body_whatsapp': b.get('body_whatsapp', '')
        }

with open('c:/users/yarleyc/documents/new opencode project/resultado_codigo.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=True, indent=2)

for k, v in result.items():
    code = v.get('code', '')
    print(f'{k} {v["name"]}: text_match={v["text_match"]} bot_key={v.get("bot_key","N/A")}')
    print(f'  code (first 200 chars): {json.dumps(code[:200], ensure_ascii=True)}')
    print(f'  body_whatsapp: {json.dumps(v["body_whatsapp"][:100] if v["body_whatsapp"] else False, ensure_ascii=True)}')
    print()
