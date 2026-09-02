from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Try reading conversations WITHOUT active_bot_id
for conv_id in [30719, 30249, 30682, 31931, 33100]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.conversation', 'method': 'read',
            'args': [[conv_id]],
            'kwargs': {'fields': ['id', 'name', 'status']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        conv = r['result'][0]
        print(f'Conv {conv_id}: {conv.get("name")} | status={conv.get("status")}')
    else:
        print(f'Conv {conv_id}: Error - {r.get("error",{}).get("message","unknown")[:100]}')

print()

# Check if there ANY cobranza conversations with done or current status
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.conversation', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'status'],
            'domain': [['connector_id', '=', 17]],
            'limit': 10,
            'order': 'id desc'
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records = r2['result']
    if isinstance(records, dict): records = records.get('records', [])
    print('Recent cobranza conversations:')
    for conv in records:
        print(f'  Conv {conv["id"]}: {conv.get("name")} | status={conv.get("status")}')
else:
    print('Error:', r2.get('error', {}).get('message', 'unknown')[:200])
