import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Try multiple access methods
models_to_check = [
    'acrux.chat.connector',
    'acrux.chat.waba.number', 
    'acrux.chat.bot',
]

for model in models_to_check:
    # Try call_kw search_read
    resp = s.post('https://latinbien.com/web/dataset/call_kw/' + model + '/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':model,'method':'search_read',
            'args':[[]],
            'kwargs':{'fields':['id','display_name'],'limit':5}
        }
    })
    data = resp.json()
    result = data.get('result')
    if result is None:
        err = data.get('error', {}).get('data', {}).get('message', 'unknown')[:200]
        print(f"{model}: ACCESS ERROR - {err}")
    else:
        print(f"{model}: {len(result)} records")
        for r in result:
            print(f"  {r}")
