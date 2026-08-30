import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Try reading bot log with minimal fields
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'log', 'create_date'],
            'domain': [],
            'limit': 20,
            'order': 'id desc'
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict):
        records = records.get('records', [])
    print(f'=== Bot Logs ({len(records)}) ===')
    for log in records:
        print(f'  ID {log["id"]}: {log.get("name","")[:50]} | {log.get("log","")[:100]} | {log.get("create_date")}')
else:
    print('Error reading bot.log:', r.get('error', {}).get('message', 'unknown')[:200])
    # Let me check the model's readable fields
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/fields_get', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot.log', 'method': 'fields_get',
            'args': [],
            'kwargs': {'attributes': ['string', 'type']}
        }
    })
    fields = resp2.json().get('result', {})
    print('Fields on bot.log:', list(fields.keys())[:15])
