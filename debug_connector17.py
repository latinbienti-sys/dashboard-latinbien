import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Try to get connector 17 info using minimal fields step by step
# First get all fields
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/fields_get', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'fields_get',
        'args': [],
        'kwargs': {'attributes': ['string', 'type', 'help']}
    }
})
fields = resp.json().get('result', {})
print('=== Connector fields with source/phone ===')
for fname, finfo in sorted(fields.items()):
    if any(kw in fname.lower() for kw in ['source', 'phone', 'number', 'account', 'status', 'active', 'bot', 'token', 'uuid']):
        print(f'  {fname}: {finfo.get("string")} ({finfo.get("type")})')

print()

# Try reading connector 17 with just the 'id' field
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id'],
            'domain': [['id', '=', 17]]
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    print('Connector 17 reads OK with just id field')
else:
    print('Connector 17 read error:', r2.get('error', {}).get('message', 'unknown'))

# Try with different fields one at a time
test_fields = ['name', 'source', 'connector_type', 'active', 'ca_status', 'token', 'uuid']
for f in test_fields:
    resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.connector', 'method': 'search_read',
            'args': [],
            'kwargs': {
                'fields': ['id', f],
                'domain': [['id', '=', 17]]
            }
        }
    })
    if 'result' in resp3.json():
        records = resp3.json()['result']
        if isinstance(records, dict):
            records = records.get('records', [])
        if records:
            print(f'  Field {f}: {records[0].get(f)}')
    else:
        print(f'  Field {f}: ERROR')
