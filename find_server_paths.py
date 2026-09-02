import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Try to read the source file from server filesystem
# First, check if there's an ir.config.parameter with the addons path
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.config_parameter/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.config_parameter', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['key', 'value'],
            'domain': [['key', 'in', ['addons_path', 'server_path', 'root_path']]],
            'limit': 5
        }
    }
})
r = resp.json()
print('Config params:', json.dumps(r, indent=2, default=str)[:500])
print()

# Try to read Bot.py via server command
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/ir.config_parameter/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.config_parameter', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['key', 'value'],
            'domain': [['key', 'ilike', '%path%']],
            'limit': 20
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records = r2['result']
    if isinstance(records, dict): records = records.get('records', [])
    print('Path-related config params:')
    for rec in records:
        print(f"  {rec['key']} = {rec.get('value', 'N/A')[:100]}")
