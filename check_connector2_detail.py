import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read connector 2 details
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.connector','method':'read',
        'args':[[2]],
        'kwargs':{'fields':['id','name','type','bot_id','message','keyword','active','start_message','start_greeting']}
    }
})
print("Connector 2:")
for c in resp.json().get('result', []):
    for k,v in c.items():
        print(f"  {k}: {repr(v)[:200]}")
    print()

# Also check ALL fields available
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/fields_get', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.connector','method':'fields_get',
        'args':[[]],'kwargs':{'attributes':['string','type','relation','help']}
    }
})
fields = resp.json().get('result', {})
print("\nAll fields:")
for fname, finfo in sorted(fields.items()):
    if fname not in ['id','__last_update','display_name','create_uid','write_uid','create_date','write_date']:
        print(f"  {fname}: {finfo.get('string','?')} ({finfo.get('type','?')})")
