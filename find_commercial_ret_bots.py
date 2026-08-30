import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Find all children of bot 61 (CATCHER COMERCIAL)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'text_match', 'code'],
            'domain': [['parent_id', '=', 61]],
            'limit': 50
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Children of bot 61 (CATCHER COMERCIAL): {len(records)} bots')
    print()
    for bot in records:
        code = bot.get('code') or ''
        has_ret = 'ret =' in code or 'ret=[' in code
        lines = len(code.split('\n'))
        tm = bot.get('text_match') or '(none)'
        # Show first 100 chars of code
        preview = code[:120].replace('\n', '\\n')
        print(f'  Bot {bot["id"]}: {bot["name"]}')
        print(f'    TextMatch="{tm}" | HasRet={has_ret} | Lines={lines}')
        print(f'    Code: {preview}')
        print()
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
