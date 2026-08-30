import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Check ALL root bots and their connector_id
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'connector_id', 'active'],
            'domain': [['active', 'in', [True, False]]],
            'limit': 200
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    
    # Show root bots first
    print('=== ROOT BOTS (parent=False) ===')
    for bot in records:
        parent = bot.get('parent_id')
        if isinstance(parent, (list, tuple)):
            parent_id = parent[0] if parent else False
        else:
            parent_id = parent or False
        
        if not parent_id:
            conn = bot.get('connector_id')
            if isinstance(conn, (list, tuple)):
                conn = conn[0] if conn else 0
            else:
                conn = 0
            status = '🟢' if bot.get('active', True) else '🔴'
            print(f'  {status} Bot {bot["id"]}: {bot["name"]} | connector={conn}')
    
    print()
    print('=== COMMERCIAL TREE (bots con connector=2 o descendientes de 61) ===')
    # Show tree under bot 61
    def show_tree(bid, indent=0):
        prefix = '  ' * indent + '└─ '
        for bot in records:
            parent = bot.get('parent_id')
            if isinstance(parent, (list, tuple)):
                parent_id = parent[0] if parent else False
            else:
                parent_id = parent or False
            
            if parent_id == bid:
                conn = bot.get('connector_id')
                if isinstance(conn, (list, tuple)):
                    conn = conn[0] if conn else 0
                else:
                    conn = 0
                status = '🟢' if bot.get('active', True) else '🔴'
                print(f'{prefix}{status} Bot {bot["id"]}: {bot["name"]} | connector={conn}')
                show_tree(bot['id'], indent + 1)
    
    show_tree(61)
    print()
    show_tree(59)  # Also check motorizado tree
    
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
