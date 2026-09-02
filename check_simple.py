from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

print("Session OK")

# Simple direct search
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {
        'model': 'acrux.chat.conversation',
        'domain': [],
        'fields': ['id', 'number', 'connector_id', 'status'],
        'limit': 10,
        'order': 'write_date desc'
    }
})
print(f"\nConversations: {resp.status_code}")
data = resp.json()
print(f"Result count: {len(data.get('result', {}).get('records', []))}")
for r in data.get('result', {}).get('records', []):
    conn = r.get('connector_id')
    conn_name = f"conn_{conn[0]}" if isinstance(conn, list) else str(conn)
    print(f"  ID {r['id']}: {r['number']} conn={conn_name} status={r['status']}")
