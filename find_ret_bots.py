import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read Bot.py file content through the server - try reading all bot codes to find who uses ret=[]
# Read ALL bots with their codes
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'use_in_connector', 'parent_id'],
            'domain': [],
            'limit': 100
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    # Filter for bots that use ret = [...] pattern
    print('Bots that might return lists (use ret = [...] or ret = {...}):')
    print()
    for bot in records:
        code = bot.get('code') or ''
        if 'ret =' in code or 'ret=[' in code:
            parent = bot.get('parent_id')
            if parent and isinstance(parent, (list, tuple)):
                parent = f'{parent[0]}-{parent[1]}'
            conns = bot.get('use_in_connector')
            if conns and isinstance(conns, (list, tuple)):
                conn_names = ', '.join([f'{c[0]}-{c[1]}' for c in conns if c])
            else:
                conn_names = 'N/A'
            print(f'  Bot {bot["id"]}: {bot["name"]}')
            print(f'    Parent: {parent} | TextMatch: {bot.get("text_match")} | Connectors: {conn_names}')
            # Show first 200 chars of code
            code_preview = code[:300] if code else '(empty)'
            for line in code_preview.split('\n')[:8]:
                print(f'    | {line}')
            print()
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:300])
