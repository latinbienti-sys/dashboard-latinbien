import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Check text_match as raw value (not processed by Odoo)
# Check bots 62, 45, 34, 61, 84, 65
for bid in [62, 45, 34, 61, 84, 65, 58, 101]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[bid]],
            'kwargs':{'fields':['id','name','text_match']}
        }
    })
    b = resp.json().get('result', [None])[0]
    if b:
        tm = b.get('text_match')
        tm_repr = repr(tm)
        tm_type = type(tm).__name__
        print(f"Bot {bid:>3} ({b['name'][:45]:45}) text_match={tm_repr:20} type={tm_type}")
