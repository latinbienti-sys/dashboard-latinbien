import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Get fields of acrux.chat.message
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/fields_get', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.message','method':'fields_get',
        'args':[[]],'kwargs':{'attributes':['string','type','relation']}
    }
})
fields = resp.json().get('result', {})
print("Fields of acrux.chat.message:")
for fname, finfo in sorted(fields.items()):
    print(f"  {fname}: {finfo.get('string','?')} type={finfo.get('type','?')} rel={finfo.get('relation','')}")
