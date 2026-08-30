import requests, json, sys, datetime
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

last_hour = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()

resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'ir.logging',
        'domain':[('create_date','>=',last_hour),('level','in',['ERROR','WARNING'])],
        'fields':['name','level','message','create_date'],
        'order':'create_date desc',
        'limit':50
    }
})
data = resp.json()
print(f"Response type: {type(data.get('result'))}")
if 'error' in data:
    print("Error:", str(data['error'])[:500])
    # Try call_kw
    resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.logging/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'ir.logging','method':'search_read',
            'args':[[('create_date','>=',last_hour),('level','in',['ERROR','WARNING'])]],
            'kwargs':{'fields':['name','level','message','create_date'],
                'order':'create_date desc',
                'limit':50}
        }
    })
    data = resp.json()
    print(f"call_kw result type: {type(data.get('result'))}")
    if isinstance(data.get('result'), list):
        records = data['result']
    else:
        records = []
else:
    records = data.get('result', {}).get('records', [])

print(f"Logs desde {last_hour}: {len(records)} entries")
found = 0
for r in records:
    if isinstance(r, dict):
        msg = str(r.get('message',''))[:300]
        name = str(r.get('name',''))[:60]
        lvl = str(r.get('level',''))
        dt = str(r.get('create_date',''))[:19]
    else:
        continue
    if 'bot' in msg.lower() or 'bot' in name.lower() or '62' in msg or '61' in msg:
        found += 1
        print(f"\n[{dt}] {lvl}: {name}")
        print(f"  {msg[:300]}")
if found == 0:
    print("No matching logs found")
    # Show 3 most recent entries regardless
    print("\n3 most recent entries:")
    for r in records[:3]:
        if isinstance(r, dict):
            print(f"  [{str(r.get('create_date',''))[:19]}] {r.get('level','')}: {str(r.get('name',''))[:60]}")
            print(f"    {str(r.get('message',''))[:200]}")
