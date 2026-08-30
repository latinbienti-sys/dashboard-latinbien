import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Find bots named MENUINICIAL and all bots with 'MENU' in name
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'search_read',
        'args':[[('name','ilike','%MENU%')]],
        'kwargs':{'fields':['id','name','text_match','parent_id','code'], 'limit':30}
    }
})
print("=== Bots con MENU en nombre ===")
for b in resp.json().get('result', []):
    pid = b.get('parent_id')
    parent = f"parent={pid[0]}" if isinstance(pid, list) else "ROOT"
    print(f"  Bot {b['id']}: {b['name'][:45]} tm={b.get('text_match')} {parent} code_len={len(b.get('code',''))}")

# Also check connector 17 and 2 config via read (search_read on connector failed)
for cid in [2, 17]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.connector','method':'read',
            'args':[[cid]],
            'kwargs':{'fields':['id','name','number','apply_from','apply_to','apply_weekday','mute_minutes','active','message','bot_apply','body_whatsapp']}
        }
    })
    r = resp.json()
    if r.get('result'):
        c = r['result'][0]
        print(f"\n=== Connector {cid}: {c.get('name','')} number={c.get('number','')} ===")
        for k,v in c.items():
            if k == 'body_whatsapp' or k == 'message':
                print(f"  {k}: {str(v)[:300]}")
            else:
                print(f"  {k}: {v}")
    else:
        print(f"\nConnector {cid} read error: {str(r.get('error',{}).get('data',{}).get('message',''))[:200]}")
