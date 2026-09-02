import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

ids = [62, 58, 101, 67, 69, 71, 73, 77, 81, 82, 83, 86, 92, 93, 94, 95, 102, 103, 104, 105, 106, 107, 108, 109, 117, 120, 121, 124, 125, 122, 123, 85, 74]
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'search_read',
        'args':[[('id','in',ids)]],
        'kwargs':{'fields':['id','name','bot_key','text_match','code','body_whatsapp']}
    }
})
bots = resp.json().get('result', [])
bots.sort(key=lambda b: ids.index(b['id']))
for b in bots:
    print('='*80)
    print(f"BOT {b['id']} | {b['name']} | key={b.get('bot_key')} | tm={b.get('text_match')}")
    print('--- body_whatsapp ---')
    print(repr(b.get('body_whatsapp') or ''))
    print('--- code ---')
    print(b.get('code') or '')
    print()
