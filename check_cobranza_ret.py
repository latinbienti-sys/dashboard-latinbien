import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Check bot 45 and 40 code in detail - look at how cobranza navigates without ret
for bid in [45, 40, 44, 41, 42, 43, 46]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read','args':[[bid]],'kwargs':{'fields':['id','name','code','text_match','sequence']}}
    })
    b = resp.json()['result'][0]
    code = b.get('code','')
    has_ret = 'ret =' in code or 'ret=' in code
    print(f"Bot {bid} ({b['name']}): ret={'YES' if has_ret else 'NO'}, text_match={b['text_match'] or '(empty)'}")
    print(f"  First 300 chars: {code[:300]}")
    print()
