import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Try different model names for connectors
for model in ['acrux.chat.connector', 'acrux_chat_connector', 'whatsapp_connector', 'acrux.whatsapp.connector']:
    try:
        resp = s.post('https://latinbien.com/web/dataset/call_kw', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': model, 'method': 'search_read',
                'args': [[]],
                'kwargs': {'fields': ['id', 'name']}
            }
        })
        r = resp.json()
        if 'result' in r:
            print(f"\nModel {model}: FOUND")
            for c in r['result']:
                print(f"  ID {c['id']}: {c.get('name','?')}")
        else:
            print(f"Model {model}: {r.get('error',{}).get('data',{}).get('message','?')[:80]}")
    except Exception as e:
        print(f"Model {model}: error - {e}")

# Check bot 61 full record
print("\n=== Bot 61 full fields ===")
fields = ['id', 'name', 'connector_id', 'parent_id', 'active', 'code']
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[61]],
        'kwargs': {'fields': fields}
    }
})
print(json.dumps(resp.json().get('result', {}), indent=2))

# Check if bot has any special field like 'trigger' or 'condition' or 'filter'
print("\n=== All fields of acrux.chat.bot ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model', 'method': 'search_read',
        'args': [[('model', '=', 'acrux.chat.bot')]],
        'kwargs': {'fields': ['id', 'name', 'field_id'],
            'limit': 1}
    }
})
model_id = resp.json().get('result', [{}])[0].get('id')
if model_id:
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'ir.model.fields', 'method': 'search_read',
            'args': [[('model_id', '=', model_id)]],
            'kwargs': {'fields': ['name', 'ttype', 'field_description'],
                'limit': 50}
        }
    })
    print(f"Fields of acrux.chat.bot:")
    for f in resp2.json().get('result', []):
        print(f"  {f['name']:30} ({f['ttype']:15}) {f.get('field_description','')[:50]}")
else:
    print("Could not find model")
