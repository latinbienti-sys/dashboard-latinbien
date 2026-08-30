import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Get ALL bots for connector 2 (comercial)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'search_read',
        'args':[[('connector_id','=',2)]],
        'kwargs':{'fields':['id','name','text_match','parent_id','sequence','bot_key','code','body_whatsapp','active'],
            'order':'sequence','limit':80}
    }
})
bots = resp.json().get('result', [])
print(f"=== BOTS CONECTOR 2 ({len(bots)}) ===")
by_id = {b['id']: b for b in bots}
for b in sorted(bots, key=lambda x: (x.get('parent_id') or [0])[0] if isinstance(x.get('parent_id'), list) else 0, reverse=False):
    pid = b.get('parent_id')
    parent = f"{pid[0]}:{by_id.get(pid[0],{}).get('name','?')[:25]}" if isinstance(pid, list) and pid else "ROOT"
    print(f"Bot {b['id']}: seq={b.get('sequence')} parent={parent}")
    print(f"   name={b['name'][:45]} tm={b.get('text_match')} key={b.get('bot_key')} active={b.get('active')}")
    msg = b.get('body_whatsapp') or ''
    print(f"   msg({len(msg)}): {str(msg)[:100]}")
    code = b.get('code','')
    print(f"   code({len(code)}): {str(code)[:80]}")
    print()
