import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Fix 63 and 64 (ret = [] -> ret = env['acrux.chat.bot'])
for bid in [63, 64, 87]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    r = resp.json()
    if 'result' not in r or not r['result']:
        continue
    code = r['result'][0].get('code', '')
    new_code = code.replace('ret = []', "ret = env['acrux.chat.bot']", 1)
    
    try:
        compile(new_code, '<string>', 'exec')
        resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[bid], {'code': new_code}], 'kwargs': {}
            }
        })
        print(f'✅ Bot {bid} fixed' if resp2.json().get('result') else f'❌ Bot {bid} error')
    except:
        print(f'❌ Bot {bid} syntax error')

# Now read full codes of CONVENIO bots (85, 74, 95, 86)
print()
for bid in [85, 74, 95, 86]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    r = resp.json()
    if 'result' not in r or not r['result']:
        continue
    code = r['result'][0].get('code', '')
    print(f'=== Bot {bid}: {r["result"][0]["name"]} ===')
    print(code)
    print()
