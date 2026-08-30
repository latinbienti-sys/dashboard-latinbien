import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# List connectors
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.connector','method':'search_read',
        'args':[[]],
        'kwargs':{'fields':['id','name','number','connector_type','active'], 'limit':40}
    }
})
print("=== CONNECTORS ===")
for r in resp.json().get('result', []):
    print(f"  ID {r['id']}: {r.get('name','')} number={r.get('number','')} type={r.get('connector_type','')} active={r.get('active')}")

# Now search conversations by connector using search first
for cid in [2, 17]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.conversation','method':'search',
            'args':[[('connector_id','=',cid)]],
            'kwargs':{'limit':8, 'order':'write_date desc'}
        }
    })
    ids = resp.json().get('result', [])
    print(f"\nConnector {cid} conv IDs: {ids}")
