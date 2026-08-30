import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Simpler approach: read conversation details directly
# Look up the conversation IDs from the bot.log entries
# Log 25761 references conversation(30719,)
# Log 25755 references conversation(31931,)

for conv_id in [30719, 30249, 30682, 31931, 33100]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.conversation', 'method': 'read',
            'args': [[conv_id]],
            'kwargs': {'fields': ['id', 'name', 'number', 'status', 'connector_id', 'active_bot_id']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        conv = r['result'][0]
        active_bot = conv.get('active_bot_id')
        if isinstance(active_bot, (list, tuple)):
            active_bot = f'{active_bot[0]}-{active_bot[1]}' if active_bot else 'None'
        conn = conv.get('connector_id')
        if isinstance(conn, (list, tuple)):
            conn = f'{conn[0]}-{conn[1]}' if conn else 'None'
        print(f'Conv {conv_id}: {conv.get("name")} ({conv.get("number")}) | status={conv.get("status")} | connector={conn} | active_bot={active_bot}')
    else:
        print(f'Conv {conv_id}: Error reading')
print()

# Now let's check what active_bot cobranza conversations have
# Let's look at NEW conversations (status=new) on cobranza
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.conversation', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'status', 'active_bot_id'],
            'domain': [['connector_id', '=', 17], ['status', '=', 'new']],
            'limit': 5,
            'order': 'id desc'
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records = r2['result']
    if isinstance(records, dict): records = records.get('records', [])
    print('New cobranza conversations:')
    for conv in records:
        active_bot = conv.get('active_bot_id')
        if isinstance(active_bot, (list, tuple)):
            active_bot = f'{active_bot[0]}-{active_bot[1]}' if active_bot else 'None'
        print(f'  Conv {conv["id"]}: {conv.get("name")} | status={conv.get("status")} | active_bot={active_bot}')
else:
    print('Error:', r2.get('error', {}).get('message', 'unknown')[:200])
