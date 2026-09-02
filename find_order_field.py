import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Check for x_fields or inherited fields on connector
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.model.fields/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model.fields', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['name', 'ttype', 'model_id'],
            'domain': [['model_id.model', '=', 'acrux.chat.connector'], ['name', 'ilike', '%order%']],
            'limit': 20
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Order-like fields: {len(records)}')
    for f in records:
        print(f'  {f["name"]}: {f["ttype"]} (model_id={f["model_id"]})')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])

# Also check for bot_id
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/ir.model.fields/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model.fields', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['name', 'ttype'],
            'domain': [['model_id.model', '=', 'acrux.chat.connector'], ['name', 'ilike', '%bot%']],
            'limit': 20
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records2 = r2['result']
    if isinstance(records2, dict): records2 = records2.get('records', [])
    print(f'\nBot-like fields: {len(records2)}')
    for f in records2:
        print(f'  {f["name"]}: {f["ttype"]}')

# Check the acrux.chat.bot model for order
resp3 = s.post('https://latinbien.com/web/dataset/call_kw/ir.model.fields/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model.fields', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['name', 'ttype'],
            'domain': [['model_id.model', '=', 'acrux.chat.bot'], ['name', 'ilike', '%order%']],
            'limit': 20
        }
    }
})
r3 = resp3.json()
if 'result' in r3:
    records3 = r3['result']
    if isinstance(records3, dict): records3 = records3.get('records', [])
    print(f'\nBot order-like fields: {len(records3)}')
    for f in records3:
        print(f'  {f["name"]}: {f["ttype"]}')

# Check full acrux.chat.bot model fields
resp4 = s.post('https://latinbien.com/web/dataset/call_kw/ir.model.fields/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model.fields', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['name', 'ttype'],
            'domain': [['model_id.model', '=', 'acrux.chat.bot']],
            'limit': 100
        }
    }
})
r4 = resp4.json()
if 'result' in r4:
    records4 = r4['result']
    if isinstance(records4, dict): records4 = records4.get('records', [])
    print(f'\nAll acrux.chat.bot fields:')
    for f in records4:
        print(f'  {f["name"]}: {f["ttype"]}')
