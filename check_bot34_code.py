from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read bot 34 code in detail
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[34]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'child_ids']}
    }
})
b34 = resp.json()['result'][0]
print(f'Bot 34: {b34["name"]}')
print(f'  text_match: {b34.get("text_match")}')
print(f'  code: repr={repr(b34["code"])}')
print(f'  child_ids: {b34.get("child_ids")}')
print()

# Also check if there's a specific order for children via sequence
print('=== Bot 34 children ordered by sequence ===')
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'text_match', 'sequence'],
            'domain': [['parent_id', '=', 34]],
            'order': 'sequence'
        }
    }
})
r = resp2.json()['result']
children = r.get('records', r) if isinstance(r, dict) else r
for c in children:
    tm = 'TEXT_MATCH' if c.get('text_match') else 'HANDLER'
    print(f'  seq={c.get("sequence"):>3} ID {c["id"]:>3}: {c["name"]} [{tm}]')
