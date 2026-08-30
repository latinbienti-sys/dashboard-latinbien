import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Check connector 2 configuration
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.connector',
        'domain':[('id','=',2)],
        'fields':['id','name','start_message','bot_id','type'],
        'limit':10
    }
})
conns = resp.json().get('result', {}).get('records', [])
print("Connector 2:")
for c in conns:
    print(f"  ID: {c['id']}")
    print(f"  Name: {c.get('name','')}")
    print(f"  Type: {c.get('type','')}")
    bot = c.get('bot_id')
    bot_info = f"bot_{bot[0]}" if isinstance(bot, list) else str(bot)
    print(f"  Bot ID: {bot_info}")
    print(f"  Start Message: {str(c.get('start_message',''))[:200]}")

# Also check whatsapp numbers for the commercial number
print("\n\nWhatsapp numbers:")
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.waba.number',
        'domain':[],
        'fields':['id','name','phone_number','bot_id','connector_id'],
        'limit':20
    }
})
nums = resp.json().get('result', {}).get('records', [])
for n in nums:
    bot = n.get('bot_id')
    conn = n.get('connector_id')
    bot_info = f"bot_{bot[0]}" if isinstance(bot, list) else "none"
    conn_info = f"conn_{conn[0]}" if isinstance(conn, list) else "none"
    print(f"  {n.get('name','')[:30]:30} phone={n.get('phone_number','')} bot={bot_info} conn={conn_info}")
