import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Find the order field type in acrux.chat.connector
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.model.fields/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model.fields', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['name', 'ttype', 'field_description', 'relation'],
            'domain': [['model_id.model', '=', 'acrux.chat.connector'], ['name', '=', 'order']],
            'limit': 10
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print('Order field details:')
    for f in records:
        print(f'  Name: {f["name"]}')
        print(f'  Type: {f["ttype"]}')
        print(f'  Relation: {f.get("relation", "N/A")}')
        print(f'  Description: {f.get("field_description", "N/A")}')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
print()

# Also check what fields exist on the connector model
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/ir.model.fields/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model.fields', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['name', 'ttype'],
            'domain': [['model_id.model', '=', 'acrux.chat.connector']],
            'limit': 100
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records2 = r2['result']
    if isinstance(records2, dict): records2 = records2.get('records', [])
    print('All fields of acrux.chat.connector:')
    for f in records2:
        print(f'  {f["name"]}: {f["ttype"]}')
