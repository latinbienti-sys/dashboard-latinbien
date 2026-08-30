import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

def read_bot(bid):
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[bid]],
            'kwargs':{'fields':['id','name','text_match','sequence','parent_id','code','body_whatsapp']}
        }
    })
    return resp.json().get('result', [None])[0]

# Find bot 45 in cobranza and bot 62 in comercial - full code
for bid in [62, 45, 34, 61]:
    b = read_bot(bid)
    if not b:
        print(f"Bot {bid}: NO ACCESS")
        continue
    pid = b.get('parent_id')
    parent = f"parent={pid[0]}" if isinstance(pid, list) else "ROOT"
    print(f"=========== Bot {bid}: {b['name']} tm={b.get('text_match')} seq={b.get('sequence')} {parent} ===========")
    print(f"--- FULL CODE ({len(b.get('code',''))} chars) ---")
    print(b.get('code',''))
    print()
