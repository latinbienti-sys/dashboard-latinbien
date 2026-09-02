from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read bot 47
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[47]],
        'kwargs': {'fields': ['id', 'name', 'parent_id', 'text_match', 'code', 'sequence']}
    }
})
b47 = resp.json()['result'][0]
print(f'Bot 47: {b47["name"]}')
print(f'  parent_id: {b47.get("parent_id")}')
print(f'  text_match: {b47.get("text_match")}')
print(f'  sequence: {b47.get("sequence")}')
print(f'  code: {repr(b47["code"][:200])}')

print()

# Also check bot 34's children with correct sequence order
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'text_match', 'sequence'],
            'domain': [['parent_id', '=', 34]],
            'order': 'sequence asc, id asc'
        }
    }
})
r = resp2.json()['result']
children = r.get('records', r) if isinstance(r, dict) else r
print('=== All children of bot 34 (CATCHER COBRANZA) ===')
for c in children:
    tm = 'TEXT_MATCH' if c.get('text_match') else 'HANDLER'
    print(f'  seq={c.get("sequence", 0):>3} ID {c["id"]:>3}: {c["name"]} [{tm}]')
