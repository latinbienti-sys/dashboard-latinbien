import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# First just check if messages exist for conv 33146
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.message',
        'domain':[('conversation_id','=',33146)],
        'fields':['id','text','create_date','from_me'],
        'order':'create_date asc',
        'limit':10
    }
})
print("Full response:", json.dumps(resp.json(), indent=2)[:2000])
print()
print("Result type:", type(resp.json().get('result')))
