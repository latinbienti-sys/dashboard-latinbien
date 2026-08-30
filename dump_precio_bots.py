# -*- coding: utf-8 -*-
import requests, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
API = 'https://latinbien.com/web/dataset/call_kw'
def call(model, method, args, kwargs=None):
    resp = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return resp.json().get('result')

for bid in [62, 86, 106, 107, 108, 109, 117, 122, 123, 124, 125]:
    r = call('acrux.chat.bot', 'read', [[bid]], {'fields': ['id', 'name', 'bot_key', 'text_match', 'parent_id', 'child_ids', 'code']})
    b = r[0]
    print(f"\n{'='*80}")
    print(f"BOT {b['id']}: {b['name']}  key={b.get('bot_key')} tm={b.get('text_match')!r}")
    print(f"parent={b.get('parent_id')} childs={b.get('child_ids')}")
    print(f"{'='*80}")
    print(b.get('code') or '(sin code)')
