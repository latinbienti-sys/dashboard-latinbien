import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

def get_msgs(cid, label):
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.message','method':'search_read',
            'args':[[('contact_id','=',cid)]],
            'kwargs':{'fields':['id','text','from_me','create_date','event','error_msg'],
                'order':'create_date asc','limit':40}
        }
    })
    msgs = resp.json().get('result', [])
    print(f"\n=== {label} (conv {cid}) - {len(msgs)} msgs ===")
    for m in msgs:
        direction = ">>ENV" if m.get('from_me') else "<<REC"
        ev = m.get('event') or ''
        err = m.get('error_msg') or ''
        txt = str(m.get('text',''))[:160].replace('\n',' | ')
        print(f"  [{m['create_date'][:19]}] {direction} {ev} {err}: {txt}")

# COBRANZA conversations (should work)
for cid in [31368, 33172]:
    get_msgs(cid, "COBRANZA")

# COMERCIAL conversations
for cid in [33170, 33169]:
    get_msgs(cid, "COMERCIAL")
