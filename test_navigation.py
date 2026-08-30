import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# 1) Test writing active_bot_id to a conversation
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/write', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'write',
        'args':[[33152], {'active_bot_id': 62}],'kwargs':{}
    }
})
print("write active_bot_id ->", resp.json().get('result'), str(resp.json().get('error',{}).get('data',{}).get('message',''))[:150])

# 2) Read bot 46 (EXIT) full code - uses ret syntax
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read',
        'args':[[46]],
        'kwargs':{'fields':['id','name','code','text_match']}
    }
})
b46 = resp.json().get('result', [None])[0]
if b46:
    print(f"\n=== Bot 46: {b46['name']} tm={b46.get('text_match')} ===")
    print(b46.get('code',''))
