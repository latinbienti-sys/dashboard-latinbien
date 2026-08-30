import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# First, try reading bots one by one - start with the cobranza chain
bot_ids = [34, 41, 42, 43, 44, 45, 47, 59, 61, 84]

for bid in bot_ids:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'parent_id']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        bot = r['result'][0]
        parent = bot.get('parent_id')
        if isinstance(parent, (list, tuple)):
            parent = f'{parent[0]}-{parent[1]}' if parent else 'None'
        tm = bot.get('text_match') or ''
        code = bot.get('code') or ''
        has_ret = 'ret =' in code or 'ret=[' in code
        print(f'Bot {bid}: {bot["name"]} | Parent={parent} | TextMatch={tm} | HasRet={has_ret}')
        # Show code summary
        lines = code.split('\n')
        for i, line in enumerate(lines[:6]):
            print(f'  L{i+1}: {line}')
        if len(lines) > 6:
            print(f'  ... ({len(lines)} lines total)')
        print()
    else:
        print(f'Bot {bid}: Error - {r.get("error", {}).get("message", "unknown")[:200]}')
        print()
