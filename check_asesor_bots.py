from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read full codes of bot 44 and 47
for bid in [44, 47]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'connector_id', 'active']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        bot = r['result'][0]
        print(f'=== Bot {bid}: {bot["name"]} ===')
        print(f'active={bot.get("active",True)} text_match="{bot.get("text_match","")}" connector={bot.get("connector_id")}')
        code = bot.get('code') or '(empty)'
        print(code)
        print()
