from odoo_conn import get_session

s = get_session()


# Read bot 34 (CATCHER COBRANZA)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[34]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match']}
    }
})
b34 = resp.json()['result'][0]
print('BOT 34: ' + b34['name'])
print('  text_match: ' + str(b34.get('text_match')))
print('  Code:')
if b34['code']:
    for i, line in enumerate(b34['code'].split('\n')[:20]):
        print('    L' + str(i+1) + ': ' + line)
else:
    print('    (empty)')
print()

# Read bot 34 children
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'text_match'],
            'domain': [['parent_id', '=', 34]]
        }
    }
})
r = resp2.json()['result']
children = r.get('records', r) if isinstance(r, dict) else r
print('Children of bot 34 (CATCHER COBRANZA):')
for c in children:
    tm = ' [TEXT_MATCH]' if c.get('text_match') else ''
    print('  ID ' + str(c['id']) + ': ' + c['name'] + tm)
