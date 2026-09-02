import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Read current code
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# Update display format
old_display = """\n                    lines.append('Precio: $' + '{:,.2f}'.format(precio))
                    lines.append('Inicial (30%): $' + '{:,.2f}'.format(inicial))
                    lines.append('20 cuotas de: $' + '{:,.2f}'.format(cuota))"""

new_display = """\n                    lines.append('Precio de contado: $' + '{:,.2f}'.format(precio))
                    lines.append('Precio final a credito: $' + '{:,.2f}'.format(precio_total))
                    lines.append('Inicial (30%): $' + '{:,.2f}'.format(inicial))
                    lines.append('20 cuotas de: $' + '{:,.2f}'.format(cuota))"""

if old_display in code:
    new_code = code.replace(old_display, new_display, 1)
    try:
        compile(new_code, '<string>', 'exec')
        print('Syntax OK')
    except SyntaxError as e:
        print(f'Syntax error: {e}')
        exit()
    
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - Display format updated')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('Old display not found')
    # Show what's actually there
    idx = code.find("Precio:")
    if idx >= 0:
        print('Found at', idx)
        print(repr(code[idx-20:idx+120]))
