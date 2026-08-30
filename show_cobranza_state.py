import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read full code of cobranza bots
for bid in [34, 45, 40, 41, 42, 43, 44, 46, 47]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[bid]],
            'kwargs':{'fields':['id','name','code','text_match','sequence','active']}
        }
    })
    b = resp.json().get('result', [None])[0]
    if b:
        code = b.get('code','')
        has_ret = 'ret =' in code or 'goto_and_wait' in code
        print(f"=== Bot {bid}: {b['name'][:45]} ===")
        print(f"  text_match={b.get('text_match')} seq={b.get('sequence')} active={b.get('active')}")
        print(f"  ret={'YES' if has_ret else 'NO'} | code_len={len(code)}")
        print(f"  First 200 chars: {code[:200]}")
        print()
