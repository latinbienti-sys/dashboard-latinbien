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
        'args':[[('connector_id','=',2)]],
        'kwargs':{'fields':['id','name','bot_key','text_match','parent_id','code','body_whatsapp'],'order':'sequence'}
    }
})
bots = resp.json().get('result', [])
by_id = {b['id']: b for b in bots}
print('=== BOT 62 FINAL ===')
b62 = [b for b in bots if b['id']==62][0]
print(b62['code'])
print()
print('=== VERIFICACION DE NAVEGACION (keys de destino deben existir) ===')
import re
keys_needed = set()
for b in bots:
    code = b.get('code') or ''
    for m in re.findall(r"goto_and_wait':\s*'([^']+)'", code):
        keys_needed.add(m)
    for m in re.findall(r"goto_and_send':\s*'([^']+)'", code):
        keys_needed.add(m)
    for m in re.findall(r"'goto_and_wait':\s*'([^']+)'", code):
        keys_needed.add(m)
print('Keys requeridas:', keys_needed)
existing = set(b.get('bot_key') for b in bots if b.get('bot_key'))
for k in sorted(keys_needed):
    status = 'OK' if k in existing else '*** FALTA ***'
    print(f'  {k}: {status}')
print()
print('=== HUÉRFANOS / REFERENCIAS A BOTS POR ID ===')
for b in bots:
    code = b.get('code') or ''
    for m in re.findall(r"browse\((\d+)\)", code):
        bid = int(m)
        if bid not in by_id:
            print(f"  Bot {b['id']} ({b['name']}) referencia browse({bid}) que no existe en conector 2")
