import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# First let me check exact names of bots 65,66,64,63
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read',
        'args':[[65,66,64,63]],
        'kwargs':{'fields':['id','name','bot_key']}
    }
})
for b in resp.json().get('result', []):
    print(f"Bot {b['id']}: name={b['name']!r} key={b.get('bot_key')!r}")

# Also check bot 85 (menu_recompra_convenio) and others
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read',
        'args':[[85,87,86,68,69,67,72,73,71,74,75,77,81,82,83,92,93,94,95,96]],
        'kwargs':{'fields':['id','name','text_match','sequence']}
    }
})
print("\nSub-menu children:")
for b in resp.json().get('result', []):
    tm = b.get('text_match') or '(empty)'
    print(f"  Bot {b['id']:>3}: {b['name'][:50]:<50} tm={tm:<15} seq={b.get('sequence','')}")
