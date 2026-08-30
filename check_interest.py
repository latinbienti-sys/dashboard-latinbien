import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Search for interest rate config or settings
models_to_check = ['ir.config_parameter', 'res.company', 'res.config.settings']
for model in models_to_check:
    try:
        resp = s.post('https://latinbien.com/web/dataset/call_kw/' + model + '/fields_get', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': model, 'method': 'fields_get',
                'args': [],
                'kwargs': {'attributes': ['string', 'type']}
            }
        })
        fields = resp.json()['result']
        for k in sorted(fields.keys()):
            if 'interes' in k.lower() or 'interes' in fields[k]['string'].lower() or 'rate' in k.lower() or 'tasa' in k.lower():
                print(f'{model}.{k}: {fields[k]["string"]} ({fields[k]["type"]})')
    except:
        pass

# Also check if there's a field on product that specifies the financing rate
resp = s.post('https://latinbien.com/web/dataset/call_kw/product.template/fields_get', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'fields_get',
        'args': [],
        'kwargs': {'attributes': ['string', 'type']}
    }
})
fields = resp.json()['result']
for k in sorted(fields.keys()):
    f = fields[k]
    if any(x in k.lower() or x in f['string'].lower() for x in ['interes', 'tasa', 'recargo', 'financi', 'porcentaje_cuota']):
        print(f'product.template.{k}: {f["string"]} ({f["type"]})')

print('\n--- Done searching ---')
