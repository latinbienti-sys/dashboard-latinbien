import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Get errors from last hour
import datetime
last_hour = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()

# Try the flat endpoint
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'ir.logging',
        'domain':[('create_date','>=',last_hour),('level','in',['ERROR','WARNING'])],
        'fields':['name','level','message','create_date','type'],
        'order':'create_date desc',
        'limit':50
    }
})
data = resp.json()
if 'error' in data:
    print("ir.logging not accessible via search_read")
    # Try call_kw
    resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.logging/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'ir.logging','method':'search_read',
            'args':[[('create_date','>=',last_hour),('level','in',['ERROR','WARNING'])]],
            'kwargs':{'fields':['name','level','message','create_date','type'],
                'order':'create_date desc',
                'limit':50}
        }
    })
    data = resp.json()
    
records = data.get('result', [])
if not records and 'result' in data:
    records = data['result'].get('records', [])

print(f"Logs desde {last_hour}")
for r in records:
    msg = (r.get('message','') or '')[:300]
    name = r.get('name','')[:60]
    lvl = r.get('level','')
    dt = str(r.get('create_date',''))[:19]
    if 'bot' in msg.lower() or '62' in msg or '61' in msg or 'comercial' in msg.lower() or 'catcher' in msg.lower():
        print(f"\n[{dt}] {lvl}: {name}")
        print(f"  {msg}")
