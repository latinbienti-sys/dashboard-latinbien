from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# 1. Search for #MENUPRINCIPAL label
print('=== Searching for MENUPRINCIPAL label ===')
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'code', 'text_match', 'label'],
            'domain': [['label', '=', 'MENUPRINCIPAL']],
        }
    }
})
r2 = resp2.json()['result']
labels = r2.get('records', r2) if isinstance(r2, dict) else r2
if labels:
    for lb in labels:
        print(f'  ID {lb["id"]}: {lb["name"]} (text_match: {lb.get("text_match")}) label={lb.get("label")}')
else:
    print('  No bot found with label MENUPRINCIPAL')

print()

# 2. Check the NOT FOUND (45) code in detail
resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[45]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b45 = resp3.json()['result'][0]
print('=== Bot 45 (NOT FOUND) code ===')
print(b45['code'])
print()

# 3. Check bot 34
resp4 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[34]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b34 = resp4.json()['result'][0]
print(f'=== Bot 34 (CATCHER COBRANZA) ===')
print(f'code length: {len(b34["code"])}')
print(f'code repr: {repr(b34["code"])}')
