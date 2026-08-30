import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Connector fields
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/fields_get', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.connector','method':'fields_get',
        'args':[[]],'kwargs':{'attributes':['string','type','relation']}
    }
})
fields = resp.json().get('result', {})
print("=== acrux.chat.connector FIELDS ===")
for fname, finfo in sorted(fields.items()):
    print(f"  {fname}: {finfo.get('string','?')} ({finfo.get('type','?')}) rel={finfo.get('relation','')}")
