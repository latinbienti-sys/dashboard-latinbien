import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read bot 62 code
for bid in [62, 65, 66, 64, 63]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[bid]],
            'kwargs':{'fields':['id','name','code','text_match','sequence']}
        }
    })
    b = resp.json().get('result', [None])[0]
    if b:
        code = b.get('code','')
        print(f"=== Bot {bid}: {b['name']} ===")
        print(f"  text_match={b.get('text_match') or '(empty)'} seq={b.get('sequence')}")
        print(f"  Code ({len(code)} chars):")
        print(code[:500])
        print("...")
        print()
