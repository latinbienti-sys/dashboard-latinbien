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
        'kwargs': {'fields': ['code']}
    }
})
code = resp.json()['result'][0]['code']

# Old display block
old = ("                    lines.append('Precio de contado: $' + '{:,.2f}'.format(precio))\n"
       "                    lines.append('Precio final a credito: $' + '{:,.2f}'.format(precio_total))\n"
       "                    lines.append('Inicial (30%): $' + '{:,.2f}'.format(inicial))\n"
       "                    lines.append('20 cuotas de: $' + '{:,.2f}'.format(cuota))")

# New display block - match user's format
new = ("                    lines.append('Precio de contado: $' + '{:,.2f}'.format(precio))\n"
       "                    lines.append('Valor de Inicial ($): $' + '{:,.2f}'.format(inicial))\n"
       "                    lines.append('Monto a Financiar ($): $' + '{:,.2f}'.format(cuota * num_cuotas))\n"
       "                    lines.append('Valor de la Cuota ($): $' + '{:,.2f}'.format(cuota))\n"
       "                    lines.append('Precio Final a Credito: $' + '{:,.2f}'.format(precio_total))")

if old in code:
    new_code = code.replace(old, new, 1)
    try:
        compile(new_code, '<string>', 'exec')
        print('Syntax OK')
    except SyntaxError as e:
        print(f'Syntax error: {e}')
        lines = new_code.split('\n')
        for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
            print(f'  {i+1}: {lines[i]}')
        exit()
    
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - All 4 fields displayed')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('Old block not found')
    # Debug
    idx = code.find('Precio de contado')
    if idx >= 0:
        print('Found at', idx)
        print(repr(code[idx:idx+300]))
    else:
        print('Precio de contado not found')
        idx = code.find('Precio:')
        if idx >= 0:
            print('Precio found at', idx)
            print(repr(code[idx:idx+300]))
