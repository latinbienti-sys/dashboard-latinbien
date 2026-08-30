import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Search for ALL bots without limit
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'text_match', 'active'],
            'domain': [],
            'limit': 200
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Total bots found: {len(records)}')
    for bot in records:
        bid = bot['id']
        name = bot.get('name', '')
        active = bot.get('active', True)
        print(f'  Bot {bid}: {name} | active={active}')
        if bid in [61, 62]:
            parent = bot.get('parent_id')
            if isinstance(parent, (list, tuple)):
                parent = f'{parent[0]}-{parent[1]}' if parent else 'None'
            print(f'    *** THIS IS BOT {bid} *** Parent={parent}')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
