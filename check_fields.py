import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Check ALL fields of bot 61 and bot 34
for bid in [61, 34, 62, 45]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[bid]],
            'kwargs':{'fields':['id','name','connector_id','parent_id','text_match','sequence','bot_key','active','apply_from','apply_to','apply_weekday','mute_minutes']}
        }
    })
    b = resp.json()['result'][0]
    print(f"Bot {bid}: {b['name']}")
    for k,v in b.items():
        if k not in ['id','name']:
            print(f"  {k}: {repr(v)[:80]}")
    print()
