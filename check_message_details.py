import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read recent cobranza messages with minimal fields
# First, search for them
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.message', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'ttype', 'text', 'create_date', 'from_me', 'contact_id', 'conversation_id'],
            'domain': [['connector_id', '=', 17]],
            'limit': 10,
            'order': 'id desc'
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Latest {len(records)} cobranza messages:')
    for msg in records:
        mid = msg['id']
        ttype = msg.get('ttype', '?')
        text = str(msg.get('text', ''))[:60]
        dt = msg.get('create_date', '')
        fm = msg.get('from_me', False)
        contact = msg.get('contact_id')
        if isinstance(contact, (list, tuple)):
            contact = f'{contact[1]}' if contact and len(contact) > 1 else f'ID {contact[0]}' if contact else 'None'
        conv = msg.get('conversation_id')
        if isinstance(conv, (list, tuple)):
            conv = conv[0] if conv else None
        incoming = 'IN' if not fm else 'OUT'
        print(f'  {incoming} Msg {mid} | Type={ttype} | {dt} | Contact={contact} | Conv={conv} | "{text}"')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:300])
print()

# Check: what type of message is "Unanswered Message"?
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.message', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'ttype', 'text', 'create_date', 'from_me', 'event'],
            'domain': [['id', '>=', 823300], ['connector_id', '=', 17]],
            'limit': 10,
            'order': 'id asc'
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records2 = r2['result']
    if isinstance(records2, dict): records2 = records2.get('records', [])
    print('Messages from ID 823300+ for cobranza:')
    for msg in records2:
        mid = msg['id']
        ttype = msg.get('ttype', '?')
        event = msg.get('event', '')
        text = str(msg.get('text', ''))[:60]
        dt = msg.get('create_date', '')
        fm = msg.get('from_me', False)
        incoming = 'IN' if not fm else 'OUT'
        print(f'  {incoming} Msg {mid} | Type={ttype} Event={event} | {dt} | "{text}"')
else:
    print('Error2:', r2.get('error', {}).get('message', 'unknown')[:200])
