import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# 1. Find all WhatsApp account models
print('=== Searching for WhatsApp account/configuration ===')
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.model/search', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model', 'method': 'search',
        'args': [],
        'kwargs': {
            'domain': [['model', 'ilike', '%chat%account%']],
            'limit': 20
        }
    }
})
model_ids = resp.json()['result']
if model_ids:
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/ir.model/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'ir.model', 'method': 'read',
            'args': [model_ids],
            'kwargs': {'fields': ['id', 'model', 'name']}
        }
    })
    for m in resp2.json()['result']:
        print(f'  Model: {m["model"]} - {m["name"]}')
else:
    print('  No chat account models found')
print()

# 2. Get all children of bot 34 with their text_match patterns
print('=== Children of bot 34 (CATCHER COBRANZA) ===')
resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'text_match', 'sequence'],
            'domain': [['parent_id', '=', 34]],
            'order': 'sequence asc, id asc'
        }
    }
})
r3 = resp3.json()['result']
children = r3.get('records', r3) if isinstance(r3, dict) else r3
for c in children:
    tm = ' [TEXT_MATCH]' if c.get('text_match') else ' [HANDLER]'
    print(f'  seq={c.get("sequence", 0):>3} ID {c["id"]:>3}: {c["name"]}{tm}')

print()

# 3. Also check the specific text_match values for TEXT_MATCH bots
print('=== TEXT_MATCH patterns ===')
for c in children:
    if c.get('text_match'):
        resp4 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'read',
                'args': [[c['id']]],
                'kwargs': {'fields': ['id', 'name', 'text_match', 'text_match_type']}
            }
        })
        b = resp4.json()['result'][0]
        print(f'  ID {b["id"]}: {b["name"]}')
        print(f'     text_match: {repr(b.get("text_match"))}')
        print(f'     type: {b.get("text_match_type")}')
