import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read full codes for all problematic bots
bids = [40, 41, 74, 85, 86, 95, 107, 108, 109, 117, 122, 124, 125]
for bid in bids:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code', 'connector_id', 'parent_id']}
        }
    })
    r = resp.json()
    if 'result' not in r or not r['result']:
        continue
    b = r['result'][0]
    print(f"{'='*60}")
    print(f"Bot {bid}: {b['name']}")
    print(f"connector={b['connector_id']}, parent={b['parent_id']}")
    print(f"{'='*60}")
    print(b.get('code', ''))
    print()
