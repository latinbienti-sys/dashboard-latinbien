import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read with simplest fields possible
for mid in [823302, 823308, 823309]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.message', 'method': 'read',
            'args': [[mid]],
            'kwargs': {'fields': ['id', 'text', 'ttype']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        msg = r['result'][0]
        print(f'Msg {mid}: ttype={msg.get("ttype")} text="{msg.get("text","")}"')
    else:
        err = r.get('error', {})
        print(f'Msg {mid}: Error - {str(err.get("message",""))[:150]}')
