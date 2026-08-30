import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# FLAT endpoint - this worked before
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[],
        'fields':['id','number','connector_id','status','active_bot_id','write_date'],
        'order':'write_date desc',
        'limit':25
    }
})
records = resp.json().get('result', {}).get('records', [])
print(f"Conversaciones (flat endpoint): {len(records)}")
for r in records:
    active = r.get('active_bot_id')
    active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
    conn = r.get('connector_id')
    conn_name = f"conn_{conn[0]}" if isinstance(conn, list) else "?"
    print(f"  ID {r['id']}: {r['number']} conn={conn_name} status={r['status']} active={active_name} write={str(r.get('write_date',''))[:19]}")
