import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read ALL bots to see tree structure
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'text_match', 'active'],
            'domain': [],
            'limit': 100
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print('ALL BOTS (id, name, parent, text_match, active):')
    print()
    # Create a tree view
    bot_map = {}
    for bot in records:
        bid = bot['id']
        parent = bot.get('parent_id')
        if isinstance(parent, (list, tuple)):
            parent = parent[0] if parent else False
        bot_map[bid] = {
            'name': bot['name'],
            'parent': parent,
            'text_match': bot.get('text_match') or '',
            'active': bot.get('active', True)
        }
    
    # Print root bots and their children
    for bid, info in sorted(bot_map.items()):
        if not info['parent']:  # Root bot
            active = 'ACTIVE' if info.get('active', True) else 'INACTIVE'
            print(f'ROOT Bot {bid}: {info["name"]} | TextMatch="{info["text_match"]}" | {active}')
            # Find children
            for cid, cinfo in sorted(bot_map.items()):
                if cinfo['parent'] == bid:
                    cactive = 'ACTIVE' if cinfo.get('active', True) else 'INACTIVE'
                    print(f'  └─ Bot {cid}: {cinfo["name"]} | TextMatch="{cinfo["text_match"]}" | {cactive}')
            print()
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
