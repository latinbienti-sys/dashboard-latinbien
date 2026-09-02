import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get ALL bots with their parent, text_match, code, active, sequence
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'text_match', 'active', 'sequence'],
            'domain': [],
            'limit': 200
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Total bots: {len(records)}')
    print()
    # Build tree
    roots = []
    children_map = {}
    for bot in records:
        bid = bot['id']
        name = bot['name']
        parent = bot.get('parent_id')
        if isinstance(parent, (list, tuple)):
            parent_id = parent[0] if parent else False
        else:
            parent_id = parent or False
        
        bot_info = f'Bot {bid}: {name}'
        if bot.get('text_match'):
            bot_info += f' [text_match={bot["text_match"]}]'
        if not bot.get('active', True):
            bot_info += ' [INACTIVE]'
        bot_info += f' (seq={bot.get("sequence",0)})'
        
        if parent_id:
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(bot_info)
        else:
            roots.append(bot_info)
    
    print('=== ROOT BOTS ===')
    for r in roots:
        print(f'  {r}')
    
    print()
    print('=== CHILDREN ===')
    for pid, children in sorted(children_map.items()):
        print(f'Parent {pid}:')
        # Find parent name
        parent_name = '?'
        for bot in records:
            if bot['id'] == pid:
                parent_name = bot['name']
                break
        print(f'  ({parent_name})')
        for child in sorted(children):
            print(f'    └─ {child}')
        print()
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
