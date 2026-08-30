import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read specific messages one at a time with basic fields
for mid in [823302, 823308, 823309]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.message', 'method': 'read',
            'args': [[mid]],
            'kwargs': {'fields': ['id', 'text', 'ttype', 'event', 'conversation_id', 'from_me', 'create_date']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        msg = r['result'][0]
        conv = msg.get('conversation_id')
        if isinstance(conv, (list, tuple)):
            conv = conv[0] if conv else None
        print(f'Msg {mid}: {msg.get("ttype")} Event={msg.get("event")} conv={conv} from_me={msg.get("from_me")}')
        print(f'  Text: "{msg.get("text","")}"')
        print(f'  Date: {msg.get("create_date")}')
        
        # If there's a conversation ID, check it
        if conv:
            resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
                'jsonrpc': '2.0', 'method': 'call',
                'params': {'model': 'acrux.chat.conversation', 'method': 'read',
                    'args': [[conv]],
                    'kwargs': {'fields': ['id', 'name', 'status']}
                }
            })
            r2 = resp2.json()
            if 'result' in r2 and r2['result']:
                conv_data = r2['result'][0]
                print(f'  -> Conv {conv}: {conv_data.get("name")} status={conv_data.get("status")}')
        print()
    else:
        print(f'Msg {mid}: Error - {r.get("error",{}).get("message","")[:100]}')
