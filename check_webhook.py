import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Try reading bot.log with just 'id'
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['id'], 'domain': [], 'limit': 5}
    }
})
r = resp.json()
print('bot.log with id only:', json.dumps(r, indent=2)[:300])

print()

# Also check if the webhook endpoint for cobranza is correct
# The connector has odoo_url field
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'odoo_url', 'endpoint'],
            'domain': [['id', '=', 17]]
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records = r2['result']
    if isinstance(records, dict):
        records = records.get('records', [])
    if records:
        print(f'Connector 17 odoo_url: {records[0].get("odoo_url")}')
        print(f'Connector 17 endpoint: {records[0].get("endpoint")}')
else:
    print('Error:', r2.get('error', {}).get('message', 'unknown'))
