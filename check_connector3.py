import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read connector 17 using search_read
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'source', 'connector_type', 'active'],
            'domain': [['id', 'in', [2, 17]]]
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict):
        records = records.get('records', [])
    for rec in records:
        print(f'Connector {rec["id"]}: {rec["name"]}')
        print(f'  source: {rec.get("source")}')
        print(f'  type: {rec.get("connector_type")}')
        print(f'  active: {rec.get("active")}')
else:
    print('ERROR:', r.get('error', {}).get('message', 'unknown'))
