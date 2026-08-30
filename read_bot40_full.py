import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read FULL code of bot 40
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read',
        'args':[[40]],
        'kwargs':{'fields':['id','name','code']}
    }
})
b = resp.json().get('result', [None])[0]
if b:
    code = b.get('code','')
    print(f"=== Bot 40: {b['name']} ===")
    print(f"Code ({len(code)} chars):")
    print(code)
    print()
    print("--- Lines ---")
    for i, line in enumerate(code.split('\n'), 1):
        print(f"{i:>3}: {line}")
