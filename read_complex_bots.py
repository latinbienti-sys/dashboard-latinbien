import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read remaining complex bots
complex_bots = [68, 72, 85, 74, 95, 75, 96, 97, 98, 99, 100, 107, 108, 109, 117, 122, 124, 125, 86, 87, 63, 64]

for bid in complex_bots:
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
        code = bot.get('code') or ''
        # Show first 200 chars
        print(f'Bot {bid}: {bot["name"]} | text_match="{bot.get("text_match","")}" | active={bot.get("active",True)} | {len(code.split(chr(10)))} líneas')
        # Check for connector 13 reference
        if 'connector_id' in code and '13' in code:
            print(f'  ⚠️ Referencia a conector 13!')
        # Show first lines
        lines = code.split('\n')
        for i, l in enumerate(lines[:6]):
            print(f'  L{i+1}: {l[:120]}')
        if len(lines) > 6:
            print(f'  ... ({len(lines)} líneas total)')
        print()
