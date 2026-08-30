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

# Bot 58 y 84: poner connector=2 (comercial) y parent=61 (catcher comercial)
# Así no son root bots, son alcanzables por navegación
if write_bot(58, {'connector_id': 2, 'parent_id': 61}):
    print("✅ Bot 58: connector=2, parent=61 (hijo de catcher, no root)")
else:
    print("❌ Bot 58 error")

if write_bot(84, {'connector_id': 2, 'parent_id': 61}):
    print("✅ Bot 84: connector=2, parent=61 (hijo de catcher, no root)")
else:
    print("❌ Bot 84 error")

# Verificar root bots actuales
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

# Verificar código de bot 61
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[61]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b = resp.json()['result'][0]
print(f"\n✅ Bot 61 code length: {len(b.get('code',''))} chars")
# Show first 200 chars
print(f"   First chars: {repr(b.get('code','')[:200])}")
