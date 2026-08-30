import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get fields of pricelist.product
resp = s.post('https://latinbien.com/web/dataset/call_kw/pricelist.product/fields_get', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'pricelist.product', 'method': 'fields_get',
        'args': [], 'kwargs': {'attributes': ['string', 'type']}
    }
})
fields = resp.json()['result']
count = 0
for k in sorted(fields.keys()):
    f = fields[k]
    print(f'{k}: {f["string"]} ({f["type"]})')
    count += 1
    if count > 30:
        print(f'... ({len(fields)} total fields)')
        break
print(f'\nTotal fields: {len(fields)}')

# Now read with all fields
all_fields = list(fields.keys())
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/pricelist.product/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'pricelist.product', 'method': 'read',
        'args': [[35501, 35502]],
        'kwargs': {'fields': all_fields}
    }
})
print(f'\nRecords:')
for r in resp2.json().get('result', []):
    print(json.dumps(r, indent=2, ensure_ascii=False))
