import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read all cobranza children (40-47) code to see if any has ret=[] set
for cid in range(40, 48):
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[cid]],
            'kwargs': {'fields': ['id', 'name', 'text_match', 'code']}
        }
    })
    if 'result' in resp.json():
        b = resp.json()['result'][0]
        has_ret = 'ret' in (b.get('code') or '')
        code_preview = (b.get('code') or '')[:100].replace('\n', ' ')
        print(f'ID {b["id"]}: {b["name"]} | text_match={b.get("text_match")} | ret={has_ret} | code={code_preview}')
    else:
        print(f'ID {cid}: ERROR reading')
