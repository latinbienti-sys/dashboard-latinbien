from odoo_conn import get_session

s = get_session()


# Check relevant fields
resp = s.post('https://latinbien.com/web/dataset/call_kw/product.template/fields_get', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'fields_get',
        'args': [],
        'kwargs': {'attributes': ['string', 'type', 'help', 'relation']}
    }
})
fields = resp.json()['result']
for k in sorted(fields.keys()):
    f = fields[k]
    if any(x in k.lower() for x in ['price_list', 'pricelist', 'product_variant', 'website_price', 'product_price']):
        print(f'{k}: {f["string"]} ({f["type"]})', end='')
        if f.get('relation'):
            print(f' -> {f["relation"]}', end='')
        print()

# Check pricelist ID 14 details
print('\n--- Pricelist 14 ---')
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/product.pricelist/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.pricelist', 'method': 'read',
        'args': [[14]],
        'kwargs': {'fields': ['id', 'name', 'currency_id', 'item_ids']}
    }
})
print(json.dumps(resp2.json()['result'][0], indent=2, ensure_ascii=False)[:500])

# Get product variant IDs for iPhone 17 Pro
print('\n--- Product variants for 2464 ---')
resp3 = s.post('https://latinbien.com/web/dataset/call_kw/product.template/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'read',
        'args': [[2464]],
        'kwargs': {'fields': ['id', 'name', 'product_variant_ids', 'product_price_list_ids']}
    }
})
print(json.dumps(resp3.json()['result'][0], indent=2, ensure_ascii=False)[:500])
