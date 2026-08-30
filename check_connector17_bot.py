import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get the bot_id and order for connector 17
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'read',
        'args': [[17]],
        'kwargs': {'fields': ['id', 'name', 'bot_id', 'order', 'source', 'token']}
    }
})
r = resp.json()
if 'result' in r and r['result']:
    conn = r['result'][0]
    print('=== Connector 17 COBRANZA ===')
    for k, v in conn.items():
        if k == 'token':
            print(f'{k}: {"***" + str(v)[-6:] if v else "N/A"}')
        else:
            print(f'{k}: {v}')
    
    # Get bot info
    bot_id = conn.get('bot_id')
    if bot_id and isinstance(bot_id, (list, tuple)) and bot_id[0]:
        resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'read',
                'args': [[bot_id[0]]],
                'kwargs': {'fields': ['id', 'name', 'code']}
            }
        })
        r2 = resp2.json()
        if 'result' in r2 and r2['result']:
            bot = r2['result'][0]
            print(f'\nBot asignado al connector: {bot["name"]} (ID {bot["id"]})')
            print(f'Code: "{bot.get("code", "")[:200]}"')
    
    # Get order bots
    order = conn.get('order') or ''
    print(f'\nOrder: {order}')
    
    order_str = str(order)
    if order_str and order_str != 'False':
        # Try to parse the order - it might be a list of IDs
        pass
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:300])
