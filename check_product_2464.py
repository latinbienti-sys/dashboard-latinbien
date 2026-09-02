from odoo_conn import get_session

s = get_session()


# Get product 2464 details
resp = s.post('https://latinbien.com/web/dataset/call_kw/product.template/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'read',
        'args': [[2464]],
        'kwargs': {'fields': ['id', 'name', 'list_price', 'x_precio_final_n8n', 'x_preciobasecatalogo',
                              'x_inicial', 'x_valor_cuotas', 'x_numero_cuotas', 'x_cuota_administrativa',
                              'x_t_referencial', 'x_costo_real_calculado', 'website_published',
                              'x_planes_cuotas', 'categ_id']}
    }
})
print('Product:')
print(json.dumps(resp.json()['result'][0], indent=2, ensure_ascii=False))

# Check plans
pid = resp.json()['result'][0]
if pid.get('x_planes_cuotas'):
    plans = pid['x_planes_cuotas']
    print(f'\nPlans: {plans}')
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/x_planes_cuotas/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'x_planes_cuotas', 'method': 'read',
            'args': [plans],
            'kwargs': {'fields': ['id', 'display_name', 'x_name', 'x_monto_inicial',
                                  'x_monto_inicial_porcentaje', 'x_valor_cuota',
                                  'x_cuotas_cvg', 'x_contrato_venta']}
        }
    })
    print('\nPlan details:')
    for p in resp2.json()['result']:
        print(json.dumps(p, indent=2, ensure_ascii=False))
        print()

# Check if there's a pricelist or website price
resp3 = s.post('https://latinbien.com/web/dataset/call_kw/product.pricelist/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.pricelist', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['id', 'name', 'currency_id'], 'limit': 10}
    }
})
print('\nPricelists:')
for pl in resp3.json()['result']:
    print(f'  {pl["id"]}: {pl["name"]}')
