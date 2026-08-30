# -*- coding: utf-8 -*-
import requests, sys, json
from collections import defaultdict
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)
s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
API = 'https://latinbien.com/web/dataset/call_kw'
def call(model, method, args, kwargs=None):
    r = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return r.json().get('result')

bots = call('acrux.chat.bot', 'search_read', [[('connector_id', '=', 2)]],
            {'fields': ['id','name','parent_id','text_match','bot_key','sequence','active','child_ids'],
             'order': 'id'})
by = {b['id']: b for b in bots}
print(f"TOTAL conector2 bots: {len(bots)}")
ch = defaultdict(list)
roots = []
for b in bots:
    p = b.get('parent_id')
    pid = p[0] if isinstance(p, (list, tuple)) and p else None
    if pid is None:
        roots.append(b['id'])
    else:
        ch[pid].append(b['id'])

def show(bid, depth=0):
    b = by[bid]
    p = b.get('parent_id')
    pid = p[0] if isinstance(p, (list, tuple)) and p else None
    tm = b.get('text_match')
    tms = (tm[:34] if isinstance(tm, str) else str(tm))
    print(('  '*depth) + f"[{bid}] {b['name']}  tm={tms!r} key={b.get('bot_key')!r} seq={b.get('sequence')} act={b.get('active')}")
    for c in sorted(ch.get(bid, []), key=lambda x: by[x].get('sequence') or 0):
        show(c, depth+1)

print("\n=== ROOTS ===")
for r in roots:
    show(r)
print("\n=== KEY MENUS (lookup by bot_key) ===")
for key in ['#COMERCIAL','#MENU_RECOMPRA','#MENU_LC_APROBADA','#No tienes linea','#Registro','#CATCHER']:
    res = call('acrux.chat.bot', 'search_read', [[('bot_key','=',key)]], {'fields':['id','name','parent_id','child_ids']})
    if res:
        b = res[0]
        print(f"  {key}: id={b['id']} name={b['name']!r} parent={b.get('parent_id')} hijos={b.get('child_ids')}")
    else:
        print(f"  {key}: (no existe)")
print("\n=== MAX ID actual en conector 2 (para elegir nuevo id) ===")
ids = [b['id'] for b in bots]
print("  max_id =", max(ids), " min_id =", min(ids))
