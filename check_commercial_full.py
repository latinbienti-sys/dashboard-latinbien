import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read commercial bots with correct fields
for bid in [61, 62, 65, 66, 64, 63, 84, 58, 101]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[bid]],
            'kwargs':{'fields':['id','name','body_whatsapp','text_match','sequence','parent_id','code','active','is_product']}
        }
    })
    b = resp.json().get('result', [None])[0]
    if not b:
        print(f"Bot {bid}: NO ACCESS - {str(resp.json().get('error',{}).get('data',{}).get('message',''))[:100]}")
        continue
    msg = b.get('body_whatsapp') or ''
    code = b.get('code','')
    pid = b.get('parent_id')
    parent = f"parent={pid[0]}" if isinstance(pid, list) else "ROOT"
    print(f"=== Bot {bid}: {b['name'][:50]} ===")
    print(f"  tm={b.get('text_match')} seq={b.get('sequence')} {parent} active={b.get('active')} prod={b.get('is_product')}")
    print(f"  MENSAJE ({len(msg)} chars): {str(msg)[:250]}")
    print(f"  CODIGO ({len(code)} chars): {code[:150]}")
    print()
