# -*- coding: utf-8 -*-
# Diagnostico cobranza (conector 17)
import requests, json, sys
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

# 1. Confirmar conectores
cons = call('acrux.chat.connector', 'search_read', [[]], {'fields': ['id', 'name']})
print('=== CONECTORES ===')
for c in cons:
    print(f"  {c['id']}: {c['name']}")

# 2. Bots del conector 17
bots = call('acrux.chat.bot', 'search_read', [[('connector_id', '=', 17)]],
            {'fields': ['id', 'name', 'text_match', 'parent_id', 'sequence', 'bot_key', 'code', 'body_whatsapp', 'active'],
             'order': 'sequence'})
print(f'\n=== BOTS CONECTOR 17 ({len(bots)}) ===')
by_id = {b['id']: b for b in bots}
for b in bots:
    pid = b.get('parent_id')
    parent = f"{pid[0]}:{by_id.get(pid[0],{}).get('name','?')[:25]}" if isinstance(pid, list) and pid else "ROOT"
    code = b.get('code') or ''
    flags = []
    if 'conversation_id' in code: flags.append('conversation_id!')
    if 'active_bot_id' in code: flags.append('active_bot_id!')
    if 'mess_id.text' not in code and 'text' in code: pass
    print(f"Bot {b['id']}: seq={b.get('sequence')} parent={parent} tm={b.get('text_match')} key={b.get('bot_key')} active={b.get('active')} {' '.join(flags)}")
    print(f"   name={b['name'][:50]}")
    print(f"   msg({len(b.get('body_whatsapp') or '')}): {str(b.get('body_whatsapp') or '')[:80]}")
    print(f"   code({len(code)}): {str(code)[:90]}")
