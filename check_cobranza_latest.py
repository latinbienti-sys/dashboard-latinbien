import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Check the latest message in cobranza
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.message', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'text', 'create_date', 'conversation_id', 'direction'],
            'domain': [['connector_id', '=', 17]],
            'limit': 3,
            'order': 'id desc'
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Latest {len(records)} messages in cobranza:')
    for msg in records:
        mid = msg['id']
        dt = msg.get('create_date', '')
        text = str(msg.get('text', ''))[:80]
        conv = msg.get('conversation_id')
        if isinstance(conv, (list, tuple)):
            conv = f'{conv[0]}' if conv else 'None'
        direction = msg.get('direction', '')
        print(f'  Msg {mid} | {dt} | Dir={direction} | Conv={conv} | "{text}"')
else:
    err = r.get('error', {}).get('message', 'unknown')[:200]
    if 'null value in column' in str(err):
        print('ERROR: null value in column - cannot read messages')
    else:
        print('Error:', err)
print()

# Try searching for specific cobranza conversations by number
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.conversation', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'number', 'connector_id', 'status'],
            'domain': [['connector_id', '=', 17]],
            'limit': 5,
            'order': 'id desc'
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records2 = r2['result']
    if isinstance(records2, dict): records2 = records2.get('records', [])
    print(f'Latest {len(records2)} conversations in cobranza:')
    for conv in records2:
        cid = conv['id']
        name = conv.get('name', '')
        number = conv.get('number', '')
        status = conv.get('status', '')
        print(f'  Conv {cid} | {name} | {number} | Status={status}')
else:
    err2 = r2.get('error', {}).get('message', 'unknown')[:200]
    print('Error reading conversations:', err2)
