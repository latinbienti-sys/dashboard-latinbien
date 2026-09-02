# -*- coding: utf-8 -*-
from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

API = 'https://latinbien.com/web/dataset/call_kw'
def call(model, method, args, kwargs=None):
    resp = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return resp.json().get('result')

for bid in [106, 117, 122]:
    r = call('acrux.chat.bot', 'read', [[bid]], {'fields': ['id', 'name', 'code']})
    b = r[0]
    print(f"\n{'='*70}\nBOT {b['id']}: {b['name']}\n{'='*70}")
    print((b.get('code') or '')[:900])
