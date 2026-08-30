import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get ALL field names of acrux.chat.message  
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.model.fields/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model.fields', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['name', 'ttype', 'field_description'],
            'domain': [['model_id.model', '=', 'acrux.chat.message']],
            'limit': 50
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print('Fields of acrux.chat.message:')
    for f in records:
        print(f'  {f["name"]} ({f["ttype"]}): {f.get("field_description","")}')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
print()

# Now read the recent cobranza messages with more fields
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.message', 'method': 'read',
        'args': [[823326, 823322, 823318, 823315, 823314]],
        'kwargs': {'fields': ['id', 'text', 'create_date', 'conversation_id', 'from_me', 'ttype']}
    }
})
r2 = resp2.json()
if 'result' in r2:
    records2 = r2['result']
    if isinstance(records2, dict): records2 = records2.get('records', [])
    print(f'Message details:')
    for msg in records2:
        print(f'  Msg {msg["id"]}:')
        print(f'    Text: "{msg.get("text","")}"')
        print(f'    Type: {msg.get("ttype")}')
        print(f'    FromMe: {msg.get("from_me")}')
        conv = msg.get('conversation_id')
        if isinstance(conv, (list, tuple)):
            print(f'    Conversation: {conv[0] if conv else None}')
        print(f'    Date: {msg.get("create_date")}')
        print()
else:
    print('Error:', r2.get('error', {}).get('message', 'unknown')[:200])
