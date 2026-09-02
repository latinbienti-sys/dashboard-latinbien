from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Check if there's a message model
for model_name in ['acrux.chat.message', 'acrux.chat.conversation', 'acrux.chat.log', 'acrux.chat.bot.log']:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.model/search', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'ir.model', 'method': 'search',
            'args': [],
            'kwargs': {'domain': [['model', '=', model_name]]}
        }
    })
    if resp.json().get('result'):
        print(f'Model {model_name} exists')

print()

# Try to read acrux.chat.message
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.message', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'text', 'create_date', 'direction'],
            'domain': [],
            'limit': 5,
            'order': 'id desc'
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records = r2['result']
    if isinstance(records, dict):
        records = records.get('records', [])
    print(f'=== Recent messages ({len(records)}) ===')
    for msg in records:
        print(f'  ID {msg["id"]}: {msg.get("text", "N/A")[:50]} | {msg.get("direction")} | {msg.get("create_date")}')
else:
    print('No message access or error')
    print(json.dumps(r2.get('error', {}), indent=2)[:300])
