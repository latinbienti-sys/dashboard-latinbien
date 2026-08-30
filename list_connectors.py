import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Search for connector 13 with minimal fields
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'source'],
            'domain': [],
            'limit': 50
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print('All connectors:')
    for c in records:
        print(f'  ID {c["id"]}: {c["name"]} | source={c.get("source","")}')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
