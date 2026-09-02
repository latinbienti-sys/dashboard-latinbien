from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Check bot 45 parent
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[45]],
        'kwargs': {'fields': ['id', 'name', 'parent_id', 'text_match', 'code']}
    }
})
b45 = resp.json()['result'][0]
print(f'Bot 45: {b45["name"]}')
print(f'  parent_id: {b45.get("parent_id")}')
print(f'  text_match: {b45.get("text_match")}')
print(f'  code: {repr(b45["code"])}')
print()

# Also check if bot 34 has 45 in child_ids
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[34]],
        'kwargs': {'fields': ['id', 'name', 'child_ids']}
    }
})
b34 = resp2.json()['result'][0]
print(f'Bot 34 child_ids: {b34.get("child_ids")}')
print(f'Is 45 in children? {45 in (b34.get("child_ids") or [])}')
