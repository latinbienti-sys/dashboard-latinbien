import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Try to get connector records via search_read with minimal fields
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name'],
            'domain': [],
            'limit': 50
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict):
        records = records.get('records', [])
    print('=== Connectors found ===')
    for rec in records:
        print(f'  ID {rec["id"]}: {rec["name"]}')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown'))

print()

# Search for the phone number +584247391810 or 584247391806
# Check acrux.chat.instance or whatever model stores phone numbers
for model_name in ['acrux.chat.instance', 'acrux.chat.whatsapp', 'acrux.chat.line', 'acrux.chat.account']:
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/ir.model/search', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'ir.model', 'method': 'search',
            'args': [],
            'kwargs': {'domain': [['model', '=', model_name]]}
        }
    })
    if resp2.json().get('result'):
        print(f'Model {model_name} exists')
        # Try reading
        resp3 = s.post(f'https://latinbien.com/web/dataset/call_kw/{model_name}/search_read', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': model_name, 'method': 'search_read',
                'args': [],
                'kwargs': {'fields': [], 'domain': [], 'limit': 5}
            }
        })
        if 'result' in resp3.json():
            print(f'  Records found: {len(resp3.json()["result"])}')

print()

# Let me check if the connector 17 source field can be read differently
# Try through the bot's connector_id field
resp4 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'connector_id'],
            'domain': [['connector_id', '=', 17]],
            'limit': 5
        }
    }
})
r4 = resp4.json().get('result', [])
if isinstance(r4, dict):
    r4 = r4.get('records', [])
print('=== Bots with connector 17 ===')
for b in r4:
    print(f'  Bot {b["id"]}: {b["name"]}')
