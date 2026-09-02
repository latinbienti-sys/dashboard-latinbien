from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Check connector configuration
print("=== Connectors ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'search_read',
        'args': [[]],
        'kwargs': {'fields': ['id', 'name', 'active']}
    }
})
for c in resp.json().get('result', []):
    print(f"  Connector {c['id']}: {c['name']} active={c['active']}")

# Check all bots that have connector_id = 2 directly
print("\n=== Bots with connector_id=2 ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[('connector_id', '=', 2)]],
        'kwargs': {'fields': ['id', 'name', 'parent_id', 'connector_id']}
    }
})
for b in resp.json().get('result', []):
    pid = b['parent_id'][0] if b['parent_id'] else 'root'
    print(f"  Bot {b['id']:>3}: {b['name'][:50]:<50} parent={pid}")

# Check ALL bots parent structure for connector 2
print("\n=== Complete tree for connector 2 ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[]],
        'kwargs': {'fields': ['id', 'name', 'parent_id', 'connector_id'],
            'order': 'parent_id'}
    }
})
# Build tree
bots_by_id = {}
for b in resp.json().get('result', []):
    bots_by_id[b['id']] = b

# Print root bots first
print("ROOT BOTS:")
for bid, b in sorted(bots_by_id.items()):
    if not b['parent_id']:
        conn = b['connector_id'][0] if b['connector_id'] else 'GLOBAL'
        print(f"  [{conn}] Bot {bid}: {b['name']}")
        # Print children
        for bid2, b2 in sorted(bots_by_id.items()):
            if b2['parent_id'] and b2['parent_id'][0] == bid:
                conn2 = b2['connector_id'][0] if b2['connector_id'] else 'GLOBAL'
                print(f"    └── [{conn2}] Bot {bid2}: {b2['name']}")
                # Grandchildren
                for bid3, b3 in sorted(bots_by_id.items()):
                    if b3['parent_id'] and b3['parent_id'][0] == bid2:
                        conn3 = b3['connector_id'][0] if b3['connector_id'] else 'GLOBAL'
                        print(f"          └── [{conn3}] Bot {bid3}: {b3['name']}")

# Check if there are inactive conversations blocking
print("\n=== Active conversations on connector 2 ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.conversation', 'method': 'search_read',
        'args': [[('connector_id', '=', 2), ('status', '=', 'current')]],
        'kwargs': {'fields': ['id', 'number', 'status', 'active_bot_id', 'create_date'],
            'limit': 10}
    }
})
for c in resp.json().get('result', []):
    bot_name = ''
    if c.get('active_bot_id'):
        bot_name = f" bot_id={c['active_bot_id'][0]}"
    print(f"  #{c['id']}: {c['number']} status={c['status']} created={c['create_date'][:19]}{bot_name}")
