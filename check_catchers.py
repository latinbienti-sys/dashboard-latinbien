from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read bot 34 (cobranza catcher), bot 58, bot 61, bot 84
for bid in [34, 58, 61, 84]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code', 'connector_id', 'parent_id']}
        }
    })
    b = resp.json()['result'][0]
    print(f"{'='*60}")
    print(f"Bot {bid}: {b['name']}")
    print(f"connector={b['connector_id']}, parent={b['parent_id']}")
    print(f"{'='*60}")
    code = b.get('code', '')
    print(repr(code))
    print()

# Also check the children of bot 34 (cobranza catcher)
print("=== Children of Bot 34 (cobranza catcher) ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[('parent_id', '=', 34)]],
        'kwargs': {'fields': ['id', 'name', 'connector_id']}
    }
})
for b in resp.json().get('result', []):
    conn = b['connector_id'][0] if b['connector_id'] else 'GLOBAL'
    print(f"  Bot {b['id']:>3}: {b['name'][:50]:<50} connector={conn}")

print()
print("=== Children of Bot 61 (commercial catcher) ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[('parent_id', '=', 61)]],
        'kwargs': {'fields': ['id', 'name', 'connector_id']}
    }
})
for b in resp.json().get('result', []):
    conn = b['connector_id'][0] if b['connector_id'] else 'GLOBAL'
    print(f"  Bot {b['id']:>3}: {b['name'][:50]:<50} connector={conn}")
