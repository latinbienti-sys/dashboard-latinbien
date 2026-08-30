import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read connectors with call_kw
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.connector','method':'search_read',
        'args':[[]],
        'kwargs':{'fields':['id','name','message','ca_status'],'limit':10}
    }
})
data = resp.json()
print("Connectors via call_kw:")
for c in data.get('result', []):
    print(f"  ID {c['id']}: {c['name']} status={c.get('ca_status','?')}")
    msg = c.get('message','')
    if msg:
        print(f"    message: {str(msg)[:200]}")

# Check conversations on connector 2 to see current state
print("\n\nConversaciones activas en connector 2:")
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[('connector_id','=',2),('status','=','current')],
        'fields':['id','number','status','active_bot_id','last_message_date'],
        'limit':10
    }
})
records = resp.json().get('result', {}).get('records', [])
for r in records:
    active = r.get('active_bot_id')
    active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
    print(f"  Conv {r['id']}: {r['number']} active={active_name}")

# Check if there are pending messages on connector 2
print("\nMensajes recientes en connector 2:")
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.message',
        'domain':[('connector_id','=',2)],
        'fields':['id','text','create_date','from_me','contact_id'],
        'order':'create_date desc',
        'limit':20
    }
})
records = resp.json().get('result', {}).get('records', [])
for r in records:
    conv = r.get('contact_id')
    conv_name = f"conv_{conv[0]}" if isinstance(conv, list) else "?"
    direction = ">>ENV" if r.get('from_me') else "<<REC"
    print(f"  [{str(r.get('create_date',''))[:19]}] {direction} {conv_name}: {str(r.get('text',''))[:100]}")
