import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Try just name and id
for cid in [17, 2]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.connector', 'method': 'read',
            'args': [[cid]],
            'kwargs': {'fields': ['id', 'name']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        conn = r['result'][0]
        print(f'Connector {cid}: {conn}')
    else:
        err = r.get('error', {})
        print(f'Connector {cid}: Error')
        print(json.dumps(err, indent=2, default=str)[:300])
    print()
