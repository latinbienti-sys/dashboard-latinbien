from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Let me check the connector via the acrux.chat.bot model's connector_id field
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'connector_id'],
            'domain': [['connector_id', '!=', False]],
            'order': 'id'
        }
    }
})
r = resp.json()['result']
bots_with_connector = r.get('records', r) if isinstance(r, dict) else r
print('=== Bots with connectors ===')
for b in bots_with_connector:
    conn = b.get('connector_id')
    if conn:
        print(f'  Bot {b["id"]}: {b["name"]} -> Connector {conn[0]}: {conn[1]}')

print()

# Now check what conversations exist
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.conversation', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'connector_id', 'channel', 'is_bot_active'],
            'domain': [],
            'limit': 10,
            'order': 'id desc'
        }
    }
})
r2 = resp2.json().get('result')
if r2:
    conversations = r2.get('records', r2) if isinstance(r2, dict) else r2
    print('=== Recent conversations ===')
    for conv in conversations:
        conn = conv.get('connector_id')
        conn_name = conn[1] if conn else 'N/A'
        print(f'  ID {conv["id"]}: {conv.get("name")} | connector: {conn_name} | active_bot: {conv.get("is_bot_active")}')
else:
    print('No conversation access or error')
    print('Response:', json.dumps(resp2.json(), indent=2)[:300])
