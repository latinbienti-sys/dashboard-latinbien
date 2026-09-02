import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

def write_bot(bid, data):
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], data], 'kwargs': {}
        }
    })
    return resp.json().get('result', False)

# Bot 58: remove as root bot (set connector_id to False)
if write_bot(58, {'connector_id': False}):
    print("✅ Bot 58: connector -> None (ya no es root)")
else:
    print("❌ Bot 58: no se pudo cambiar")

# Bot 61: verify it still has connector=2
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[61]],
        'kwargs': {'fields': ['id', 'name', 'connector_id']}
    }
})
b61 = resp.json()['result'][0]
print(f"Bot 61 connector = {b61['connector_id']}")

# Now only bot 61 is root for connector 2
# Check all root bots for connector 2
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[('parent_id', '=', False)]],
        'kwargs': {'fields': ['id', 'name', 'connector_id']}
    }
})
print("\n=== Root bots actuales ===")
for b in resp.json().get('result', []):
    conn = b['connector_id'][0] if b['connector_id'] else 'GLOBAL'
    print(f"  Bot {b['id']:>3}: {b['name'][:50]:<50} connector={conn}")
