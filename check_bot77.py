import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Check bot 77 connector
for bid in [77]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'parent_id', 'connector_id', 'active']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        bot = r['result'][0]
        conn = bot.get('connector_id')
        if isinstance(conn, (list, tuple)):
            conn = f'{conn[0]}-{conn[1]}' if conn else 'None'
        parent = bot.get('parent_id')
        if isinstance(parent, (list, tuple)):
            parent = f'{parent[0]}' if parent else 'None'
        print(f'Bot {bid}: {bot["name"]} | connector={conn} | parent={parent} | active={bot.get("active",True)}')
