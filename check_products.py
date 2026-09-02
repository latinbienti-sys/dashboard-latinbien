from odoo_conn import get_session

s = get_session()

# Read VALIDAR_CEDULA code - show the split part
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read',
        'args':[[62]],
        'kwargs':{'fields':['id','name','code']}
    }
})
code = resp.json()['result'][0]['code']
idx = code.find('parts = texto.split')
print('=== Splitting logic ===')
print(code[idx:idx+200])
print()

# Check if there are any products with 'nevera' in name
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/product.template/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'product.template','method':'search_read',
        'args':[[['name','ilike','%nevera%']]],
        'kwargs':{'fields':['id','name','list_price'],'limit':5}
    }
})
prods = resp2.json().get('result', [])
print('=== Products matching "nevera" ===')
if prods:
    for p in prods:
        print('  ID={} {} ${}'.format(p['id'], p['name'], p.get('list_price', 0)))
else:
    print('  No products found with "nevera" in name')
    # Show some products for reference
    resp3 = s.post('https://latinbien.com/web/dataset/call_kw/product.template/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'product.template','method':'search_read',
            'args':[[]],
            'kwargs':{'fields':['id','name','list_price'],'limit':10}
        }
    })
    print('  Sample products:')
    for p in resp3.json().get('result', []):
        print('    ID={} {} ${}'.format(p['id'], p['name'], p.get('list_price', 0)))
