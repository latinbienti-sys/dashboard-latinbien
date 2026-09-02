from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read connector 17 details
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'read',
        'args': [[17]],
        'kwargs': {
            'fields': ['id', 'name', 'source', 'ca_status', 'ca_status_text', 'odoo_url',
                       'webhook_url', 'token', 'type', 'bot_id', 'order']
        }
    }
})
r = resp.json()
if 'result' in r and r['result']:
    conn = r['result'][0]
    for k, v in conn.items():
        if k == 'token':
            print(f'{k}: {"***" + str(v)[-8:] if v else "N/A"}')
        else:
            val = str(v)
            if len(val) > 100:
                val = val[:100] + '...'
            print(f'{k}: {val}')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:300])
print()

# Read connector 2 for comparison
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'read',
        'args': [[2]],
        'kwargs': {
            'fields': ['id', 'name', 'source', 'ca_status', 'ca_status_text', 'odoo_url',
                       'webhook_url', 'token', 'type', 'bot_id', 'order']
        }
    }
})
r2 = resp2.json()
if 'result' in r2 and r2['result']:
    conn2 = r2['result'][0]
    print('=== Connector 2 (COMERCIAL - working) for comparison ===')
    for k, v in conn2.items():
        if k == 'token':
            print(f'{k}: {"***" + str(v)[-8:] if v else "N/A"}')
        else:
            val = str(v)
            if len(val) > 100:
                val = val[:100] + '...'
            print(f'{k}: {val}')
