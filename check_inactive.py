from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Get all bots, list inactive ones
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[]],
        'kwargs': {'fields': ['id', 'name', 'active', 'connector_id', 'parent_id'],
            'order': 'id'}
    }
})
bots = resp.json().get('result', [])

print(f"Total bots: {len(bots)}")
print()

# Group
inactive = [b for b in bots if not b['active']]
active = [b for b in bots if b['active']]

print(f"Active: {len(active)}")
print(f"Inactive: {len(inactive)}")

# Check connector distribution among inactive
print("\n--- Inactive bots ---")
for b in inactive:
    conn = b['connector_id'] if b['connector_id'] else 'None'
    pid = b['parent_id'][0] if b['parent_id'] else 'root'
    print(f"  Bot {b['id']:>3}: {b['name'][:30]:<30} connector={conn:<5} parent={pid}")

# Check active ones without connector (global)
print("\n--- Active bots without connector (global) ---")
for b in active:
    if not b['connector_id']:
        conn = b['connector_id'] if b['connector_id'] else 'None'
        pid = b['parent_id'][0] if b['parent_id'] else 'root'
        print(f"  Bot {b['id']:>3}: {b['name'][:30]:<30} connector={conn:<5} parent={pid}")

print("\n--- Bots with connector=2 (commercial) ---")
for b in bots:
    if b['connector_id'] and b['connector_id'][0] == 2:
        print(f"  Bot {b['id']:>3}: {b['name'][:30]:<30} active={b['active']:<5} parent={b['parent_id'][0] if b['parent_id'] else 'root'}")

print("\n--- Bots with connector=17 (cobranza) ---")
for b in bots:
    if b['connector_id'] and b['connector_id'][0] == 17:
        print(f"  Bot {b['id']:>3}: {b['name'][:30]:<30} active={b['active']:<5} parent={b['parent_id'][0] if b['parent_id'] else 'root'}")
