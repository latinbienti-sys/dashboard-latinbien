import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Search for bots with the welcome text
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'search_read',
        'args':[[]],
        'kwargs':{'fields':['id','name','code'],
            'limit':200}
    }
})
bots = resp.json().get('result', [])
print("Bots containing 'Bienvenido a Latinbien':")
for b in bots:
    code = b.get('code','') or ''
    if 'Bienvenido a Latinbien' in code:
        print(f"  Bot {b['id']}: {b['name']}")
        print(f"  Code excerpt: {code[code.find('Bienvenido'):code.find('Bienvenido')+120]}")
        print()

print("\nBots containing 'Recibido:' (echo message):")
for b in bots:
    code = b.get('code','') or ''
    if 'Recibido:' in code:
        print(f"  Bot {b['id']}: {b['name']}")
        print(f"  Code excerpt: {code[code.find('Recibido'):code.find('Recibido')+80]}")
        print()
