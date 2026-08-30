import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read the Bot.py source file - try to get it via ir.attachment or ir.model.data
# First check if it's in a known module
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.module.module/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.module.module', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'state'],
            'domain': [['name', 'ilike', '%whatsapp_connector_bot%']]
        }
    }
})
r = resp.json().get('result', [])
if r:
    records = r.get('records', r) if isinstance(r, dict) else r
    print('Module:', records)
else:
    print('Module whatsapp_connector_bot not found in ir.module.module')

# Instead, let's look at the error traceback more carefully
# The error is in /odoo/custom/addons/whatsapp_connector_bot/models/Bot.py at line 476
# Let's try to read the file via the server's file system
# Actually, let me try to get it via ir.attachment
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/ir.attachment/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.attachment', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'datas_fname', 'res_model', 'res_id'],
            'domain': [['name', 'ilike', '%Bot.py%']],
            'limit': 10
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records = r2['result']
    if isinstance(records, dict):
        records = records.get('records', [])
    print('Attachments:', records)
else:
    print('Error:', r2.get('error', {}).get('message', 'unknown'))
