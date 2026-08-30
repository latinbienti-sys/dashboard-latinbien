import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Try reading messages with minimal fields (no direction or connector_id)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.message', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'text', 'create_date'],
            'domain': [['connector_id', '=', 17]],
            'limit': 5,
            'order': 'id desc'
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Latest {len(records)} messages in cobranza (connector 17):')
    for msg in records:
        mid = msg['id']
        dt = msg.get('create_date', '')
        text = str(msg.get('text', ''))[:80]
        print(f'  Msg {mid} | {dt} | "{text}"')
else:
    err = r.get('error', {})
    print('Error reading messages:', json.dumps(err, indent=2, default=str)[:300])
print()

# NOW - let's try a DIFFERENT approach:
# Instead of searching messages by connector, search by conversation
# Get the most recent conversation and get its messages
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.conversation', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'number', 'status', 'create_date'],
            'domain': [['connector_id', '=', 17]],
            'limit': 3,
            'order': 'id desc'
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records2 = r2['result']
    if isinstance(records2, dict): records2 = records2.get('records', [])
    print('Recent conversations:')
    for conv in records2:
        cid = conv['id']
        print(f'  Conv {cid}: {conv["name"]} ({conv["number"]}) - {conv["status"]} - {conv.get("create_date")}')
        # Now get the last 2 messages for this conversation
        resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.message', 'method': 'search_read',
                'args': [],
                'kwargs': {
                    'fields': ['id', 'text', 'create_date', 'from_me'],
                    'domain': [['conversation_id', '=', cid]],
                    'limit': 2,
                    'order': 'id desc'
                }
            }
        })
        r3 = resp3.json()
        if 'result' in r3:
            msgs = r3['result']
            if isinstance(msgs, dict): msgs = msgs.get('records', [])
            for m in msgs:
                direction = 'ENVIADO' if m.get('from_me') else 'RECIBIDO'
                print(f'    Msg {m["id"]}: {direction} "{str(m.get("text",""))[:60]}" ({m.get("create_date")})')
        else:
            print(f'    Error reading messages: {r3.get("error", {}).get("message","")[:100]}')
else:
    print('Error:', r2.get('error', {}).get('message', 'unknown')[:200])
