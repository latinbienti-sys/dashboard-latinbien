import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read full codes of key handlers: recompra ones + active_bot_id ones
for bid in [68, 69, 102, 106, 83, 94, 104]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[bid]],
            'kwargs':{'fields':['id','name','text_match','bot_key','code']}
        }
    })
    b = resp.json().get('result', [None])[0]
    if not b:
        print(f"Bot {bid} NO ACCESS")
        continue
    print(f"=========== Bot {bid}: {b['name']} tm={b.get('text_match')} key={b.get('bot_key')} ===========")
    print(b.get('code',''))
    print()
