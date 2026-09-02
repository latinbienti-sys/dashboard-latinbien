from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read bot 84 (TRANSFERENCIA_ASESOR) code
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[84]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match']}
    }
})
b84 = resp.json()['result'][0]
print(f'Bot 84: {b84["name"]}')
print(f'Code:')
print(b84['code'])
print()

# Also read bot 40 (PAGAR Y REPORTAR) to compare
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[40]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b40 = resp2.json()['result'][0]
print(f'Bot 40: {b40["name"]}')
print(f'Code:')
print(b40['code'])
