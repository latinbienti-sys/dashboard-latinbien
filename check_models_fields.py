import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

def fields_get(model):
    resp = s.post('https://latinbien.com/web/dataset/call_kw/%s/fields_get' % model, json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':model,'method':'fields_get',
            'args':[[]],'kwargs':{'attributes':['string','type','relation']}
        }
    })
    return resp.json().get('result', {})

# Conversation all fields
cf = fields_get('acrux.chat.conversation')
print("=== acrux.chat.conversation FIELDS ===")
for fname, finfo in sorted(cf.items()):
    print(f"  {fname}: {finfo.get('string','?')} ({finfo.get('type','?')}) rel={finfo.get('relation','')}")

# Message fields
print("\n=== acrux.chat.message FIELDS ===")
mf = fields_get('acrux.chat.message')
for fname, finfo in sorted(mf.items()):
    print(f"  {fname}: {finfo.get('string','?')} ({finfo.get('type','?')}) rel={finfo.get('relation','')}")
