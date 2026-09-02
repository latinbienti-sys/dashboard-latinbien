import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Find which conversation has the "Hola" message and trace it
# First, find conversation_id for msg 823302
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.message', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'conversation_id', 'text', 'create_date', 'ttype', 'from_me', 'event'],
            'domain': [['id', '>=', 823300], ['id', '<=', 823320], ['connector_id', '=', 17]],
            'limit': 20,
            'order': 'id asc'
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print('Messages 823300-823320 for cobranza:')
    for msg in records:
        mid = msg['id']
        conv = msg.get('conversation_id')
        if isinstance(conv, (list, tuple)):
            conv = conv[0] if conv else None
        ttype = msg.get('ttype', '?')
        event = msg.get('event', '')
        text = str(msg.get('text', ''))[:60]
        dt = msg.get('create_date', '')
        fm = msg.get('from_me', False)
        direction = 'OUT' if fm else 'IN '
        print(f'  {direction} Msg {mid} | Conv={conv} | Type={ttype} Event={event} | {dt} | "{text}"')
        
        # If this is a text message from customer, check its conversation for more info
        if not fm and ttype == 'text':
            # Check this conversation's details
            resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
                'jsonrpc': '2.0', 'method': 'call',
                'params': {'model': 'acrux.chat.conversation', 'method': 'read',
                    'args': [[conv]],
                    'kwargs': {'fields': ['id', 'name', 'number', 'status', 'active_bot_id', 'connector_id']}
                }
            })
            r3 = resp3.json()
            if 'result' in r3 and r3['result']:
                conv_data = r3['result'][0]
                active_bot = conv_data.get('active_bot_id')
                if isinstance(active_bot, (list, tuple)):
                    active_bot = f'{active_bot[0]}-{active_bot[1]}' if active_bot else 'None'
                conn = conv_data.get('connector_id')
                if isinstance(conn, (list, tuple)):
                    conn = f'{conn[0]}-{conn[1]}' if conn else 'None'
                print(f'    -> Conv {conv}: status={conv_data.get("status")} active_bot={active_bot} connector={conn}')
            print()
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:300])
