from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read connector 17 (COBRANZA) - just basic fields
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'read',
        'args': [[17]],
        'kwargs': {'fields': ['id', 'name', 'source', 'ca_status', 'active']}
    }
})
print('Connector 17:', json.dumps(resp.json(), indent=2, default=str)[:300])

print()

# Also check if there are conversation records to see if messages are arriving
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.conversation', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'connector_id', 'active_bot_id', 'is_bot_active'],
            'domain': [['connector_id', '=', 17]],
            'limit': 5,
            'order': 'id desc'
        }
    }
})
print('Recent conversations:', json.dumps(resp2.json(), indent=2, default=str)[:500])
