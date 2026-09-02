from odoo_conn import get_session

s = get_session()


# Get fields of x_planes_cuotas
resp = s.post('https://latinbien.com/web/dataset/call_kw/x_planes_cuotas/fields_get', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'x_planes_cuotas', 'method': 'fields_get',
        'args': [],
        'kwargs': {'attributes': ['string', 'type', 'help', 'relation']}
    }
})
fields = resp.json()['result']
for k in sorted(fields.keys()):
    f = fields[k]
    print(f'{k}: {f["string"]} ({f["type"]})', end='')
    if f.get('relation'):
        print(f' -> {f["relation"]}', end='')
    print()

# Now read the 4 plans
print('\n--- Reading plans ---')
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/x_planes_cuotas/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'x_planes_cuotas', 'method': 'read',
        'args': [[40653, 40654, 40655, 40656]],
        'kwargs': {'fields': ['id', 'name', 'x_inicial', 'x_numero_cuotas', 'x_valor_cuota', 'x_interes', 'x_precio_final']}
    }
})
if 'result' in resp2.json():
    for p in resp2.json()['result']:
        print(p)
else:
    print('Error:', resp2.json().get('error', {}))
    # Try all fields
    resp3 = s.post('https://latinbien.com/web/dataset/call_kw/x_planes_cuotas/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'x_planes_cuotas', 'method': 'read',
            'args': [[40653]],
            'kwargs': {'fields': list(fields.keys())}
        }
    })
    print('\nAll fields for first plan:')
    print(json.dumps(resp3.json().get('result', resp3.json()), indent=2, ensure_ascii=False)[:2000])
