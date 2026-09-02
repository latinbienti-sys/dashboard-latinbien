from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Use the FLAT endpoint that worked before
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[],
        'fields':['id','number','connector_id','status','active_bot_id','last_message_date'],
        'order':'write_date desc',
        'limit':20
    }
})
data = resp.json()
print(f"Response type: {type(data.get('result'))}")
records = data.get('result', {}).get('records', [])
print(f"Total conversations: {len(records)}")
for r in records:
    active = r.get('active_bot_id')
    active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
    conn = r.get('connector_id')
    conn_name = f"conn_{conn[0]}" if isinstance(conn, list) else "?"
    print(f"  ID {r['id']}: {r['number']} conn={conn_name} status={r['status']} active={active_name}")
