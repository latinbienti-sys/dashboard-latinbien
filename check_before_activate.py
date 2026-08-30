import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Check Bot 58 (ACCESOS) - global active root
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[58]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'connector_id', 'active', 'parent_id']}
    }
})
r = resp.json()
if 'result' in r and r['result']:
    bot = r['result'][0]
    print(f'=== Bot 58: {bot["name"]} ===')
    print(f'active={bot.get("active",True)} text_match="{bot.get("text_match","")}"')
    code = bot.get('code') or '(empty)'
    print(f'Code:\n{code[:500]}')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:200])
print()

# Check Bot 62 VALIDAR_CEDULA for ret = [...]
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match']}
    }
})
r2 = resp2.json()
if 'result' in r2 and r2['result']:
    bot2 = r2['result'][0]
    print(f'=== Bot 62: {bot2["name"]} ===')
    code2 = bot2.get('code') or '(empty)'
    # Show last 20 lines where ret is set
    lines = code2.split('\n')
    for i, line in enumerate(lines):
        if 'ret =' in line:
            print(f'  L{i+1}: {line}')
    print(f'  (total {len(lines)} lines)')
    
    # Check for ret = [...] pattern
    if 'ret = [{' in code2:
        print('  ⚠️ USES ret = [...] - WILL CRASH server')
else:
    print('Error:', r2.get('error', {}).get('message', 'unknown')[:200])
print()

# Count all bots with connector=0 in commercial tree
resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'connector_id'],
            'domain': [['active', 'in', [True, False]], '|', ['connector_id', '=', False], ['connector_id', '=', None]],
            'limit': 50
        }
    }
})
r3 = resp3.json()
if 'result' in r3:
    records = r3['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'\nBots with connector=None/False (GLOBAL):')
    for bot in records:
        print(f'  Bot {bot["id"]}: {bot["name"]}')
