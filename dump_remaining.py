import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'search_read',
        'args':[[('id','in',[68,70,72,75,87,96,97,98,99,100,84,61,65,66,64,63])]],
        'kwargs':{'fields':['id','name','bot_key','text_match','code','body_whatsapp']}
    }
})
bots = resp.json().get('result', [])
bots.sort(key=lambda b: b['id'])
for b in bots:
    print('='*80)
    print("BOT {} | {} | key={} | tm={}".format(b['id'], b['name'], b.get('bot_key'), b.get('text_match')))
    print("--- body_whatsapp ---")
    print(repr(b.get('body_whatsapp') or ''))
    print("--- code ---")
    print(b.get('code') or '(empty)')
    print()
