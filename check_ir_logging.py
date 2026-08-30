import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Check ir.logging for recent errors
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.logging/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.logging', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'func', 'line', 'level', 'message', 'create_date'],
            'domain': [['name', 'ilike', '%cobranza%'], ['level', '=', 'error']],
            'limit': 5,
            'order': 'id desc'
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Found {len(records)} ir.logging entries:')
    for log in records:
        print(f'  Log {log["id"]} | {log.get("create_date")} | {log.get("name")}')
        print(f'    Func: {log.get("func")}:{log.get("line")}')
        msg = str(log.get('message', ''))[:200]
        print(f'    Msg: {msg}')
        print()
else:
    err = r.get('error', {}).get('message', 'unknown')[:300]
    print('Error:', err)
print()

# Also try broader search
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/ir.logging/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.logging', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'message', 'create_date'],
            'domain': [['name', 'ilike', '%bot%'], ['level', '=', 'error']],
            'limit': 5,
            'order': 'id desc'
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records2 = r2['result']
    if isinstance(records2, dict): records2 = records2.get('records', [])
    print(f'Found {len(records2)} bot-related error logs:')
    for log in records2:
        print(f'  Log {log["id"]} | {log.get("create_date")} | {log.get("name")}')
        msg = str(log.get('message', ''))[:300]
        print(f'    Msg: {msg}')
        print()
else:
    print('Error:', r2.get('error', {}).get('message', 'unknown')[:200])
