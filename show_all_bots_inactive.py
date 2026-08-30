import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Include inactive bots in the search
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'text_match', 'active', 'sequence'],
            'domain': [['active', 'in', [True, False]]],
            'limit': 200
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Total bots (including inactive): {len(records)}')
    print()
    
    # Build tree with inactive info
    roots = []
    children_map = {}
    bot_names = {}
    for bot in records:
        bid = bot['id']
        name = bot['name']
        bot_names[bid] = name
        parent = bot.get('parent_id')
        if isinstance(parent, (list, tuple)):
            parent_id = parent[0] if parent else False
        else:
            parent_id = parent or False
        
        status = 'ACTIVE' if bot.get('active', True) else 'INACTIVE'
        tm = f' [text_match={bot["text_match"]}]' if bot.get('text_match') else ''
        seq = bot.get('sequence', 0)
        info = f'Bot {bid}: {name}{tm} | {status} (seq={seq})'
        
        if parent_id:
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(info)
        else:
            roots.append(info)
    
    print('=== ROOT BOTS ===')
    for r_info in roots:
        print(f'  {r_info}')
    
    print()
    print('=== CHILDREN by Parent ===')
    for pid, children in sorted(children_map.items()):
        pname = bot_names.get(pid, 'UNKNOWN')
        print(f'Parent {pid} ({pname}):')
        for child in sorted(children):
            print(f'    └─ {child}')
        print()
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
