import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read codes of sub-menu bots (63, 64, 65, 66) and some key children
bots_to_check = [63, 64, 65, 66, 67, 68, 69, 71, 72, 73, 77, 81, 82, 83, 85, 92, 93, 94, 101, 102, 103, 104, 105, 121, 120, 118, 119]
# Also check cobranza bots 40, 41 (but don't modify them)
bots_to_check += [40, 41]

for bid in bots_to_check:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'active']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        bot = r['result'][0]
        code = bot.get('code') or '(empty)'
        lines = code.split('\n')
        ret_lines = [i+1 for i, l in enumerate(lines) if 'ret =' in l]
        print(f'Bot {bid}: {bot["name"]} | text_match="{bot.get("text_match","")}" | active={bot.get("active",True)} | {len(lines)} líneas | ret en líneas: {ret_lines}')
        # Show code if short
        if len(lines) <= 5:
            for i, l in enumerate(lines):
                print(f'  L{i+1}: {l[:120]}')
        print()
