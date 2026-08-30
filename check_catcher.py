import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read all root bots (no parent)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[('parent_id', '=', False)]],
        'kwargs': {'fields': ['id', 'name', 'active', 'connector_id', 'code'],
            'order': 'id'}
    }
})
roots = resp.json().get('result', [])
print("=== ROOT BOTS (sin parent) ===")
for b in roots:
    conn = b['connector_id'][0] if b['connector_id'] else 'GLOBAL'
    print(f"Bot {b['id']:>3}: {b['name'][:50]:<50} connector={conn:<7} active={b['active']}")

print()

# Read bot 58 and bot 61 codes
for bid in [58, 61]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code', 'connector_id', 'parent_id']}
        }
    })
    b = resp.json()['result'][0]
    print(f"{'='*60}")
    print(f"Bot {bid}: {b['name']}")
    print(f"connector={b['connector_id']}, parent={b['parent_id']}")
    print(f"{'='*60}")
    print(b.get('code', '(empty)'))
    print()
