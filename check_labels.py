from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Get all bots with their labels - read individually known bots
known_ids = [34, 45, 61, 62]
for bid in known_ids:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'label']}
        }
    })
    r = resp.json()
    if 'result' in r:
        b = r['result'][0]
        print(f'ID {b["id"]}: {b["name"]}')
        print(f'  label: {b.get("label")}')
        print(f'  text_match: {b.get("text_match")}')
        if bid == 45:
            print(f'  code: {b["code"]}')
    else:
        print(f'ID {bid}: ERROR - {r.get("error", {}).get("message", "unknown")}')
