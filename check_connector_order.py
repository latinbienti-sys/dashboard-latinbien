from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read connector 17 with just order and bot_id
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'read',
        'args': [[17]],
        'kwargs': {'fields': ['id', 'name', 'order', 'bot_id']}
    }
})
r = resp.json()
if 'result' in r and r['result']:
    conn = r['result'][0]
    print('=== CONNECTOR 17 (COBRANZA) ===')
    print(f'Name: {conn["name"]}')
    print(f'Bot ID: {conn.get("bot_id")}')
    print(f'Order: {conn.get("order")}')
    
    order_raw = conn.get('order')
    if order_raw and order_raw != 'False':
        # Order might be a string or a list
        print(f'Order type: {type(order_raw).__name__}')
        print(f'Order value: {order_raw}')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
print()

# Also read connector 2 for comparison
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.connector', 'method': 'read',
        'args': [[2]],
        'kwargs': {'fields': ['id', 'name', 'order', 'bot_id']}
    }
})
r2 = resp2.json()
if 'result' in r2 and r2['result']:
    conn2 = r2['result'][0]
    print('=== CONNECTOR 2 (COMERCIAL) ===')
    print(f'Name: {conn2["name"]}')
    print(f'Bot ID: {conn2.get("bot_id")}')
    print(f'Order: {conn2.get("order")}')
