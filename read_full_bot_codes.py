import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read full codes for bots that use ret=
for bid in [41, 44, 47, 59, 84]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        bot = r['result'][0]
        print(f'=== Bot {bid}: {bot["name"]} ===')
        code = bot.get('code') or '(empty)'
        print(code)
        print()
    else:
        err = r.get('error', {}).get('message', 'unknown')[:200]
        print(f'Bot {bid}: Error - {err}')
        print()
