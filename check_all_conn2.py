import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Check all root bots on connector 2
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.bot',
        'domain':[('parent_id','=',False),'|',('connector_id','=',2),('connector_id','=',False)],
        'fields':['id','name','text_match','sequence','active','bot_key','connector_id'],
        'limit':50
    }
})
bots = resp.json().get('result', {}).get('records', [])
print("Root bots on connector 2:")
for b in bots:
    conn = b.get('connector_id')
    conn_name = f"conn_{conn[0]}" if isinstance(conn, list) else str(conn)
    tm = str(b.get('text_match','') or '-')
    print(f"  Bot {b['id']:>3}: {b['name'][:50]:<50} tm={tm:<15} seq={b.get('sequence',0)} key={str(b.get('bot_key','') or '-')[:20]} conn={conn_name}")

# Also check ALL active bots with connector=2
print("\nALL active bots with connector=2:")
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.bot',
        'domain':[('connector_id','=',2),('active','=',True)],
        'fields':['id','name','text_match','parent_id','sequence'],
        'order':'sequence',
        'limit':100
    }
})
bots2 = resp.json().get('result', {}).get('records', [])
for b in bots2:
    pid = b.get('parent_id')
    parent = f"parent={pid[0]}" if isinstance(pid, list) else "root"
    tm = str(b.get('text_match','') or '-')
    print(f"  Bot {b['id']:>3}: {b['name'][:50]:<50} tm={tm:<15} seq={b.get('sequence',0)} {parent}")
