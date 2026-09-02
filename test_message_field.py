import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read message 823938 (the one that crashed on 13:50:44) with various fields
for flds in [['id','text','contact_id'], ['id','conversation_id'], ['id','contact_id','conversation_id']]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.message','method':'read',
            'args':[[823938]],
            'kwargs':{'fields':flds}
        }
    })
    r = resp.json()
    print(f"fields={flds} -> result={r.get('result')}")
    if r.get('error'):
        msg = r['error']['data'].get('message','')
        print(f"   ERROR: {msg[:200]}")
    print()
