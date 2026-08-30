import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# For bots that already use send_message_bus_release, just fix the ret at end
# And for bots with simple ret patterns, fix them

# Read all remaining bot codes fully
remaining = [68, 72, 75, 96, 97, 98, 99, 100, 85, 74, 95, 86, 87, 107, 108, 109, 117, 122, 124, 125, 63, 64]

for bid in remaining:
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
    lines = code.split('\n')
    
    # Find ret = lines
    ret_lines = [i for i, l in enumerate(lines) if l.strip().startswith('ret =')]
    
    if not ret_lines:
        continue  # No ret, skip
    
    print(f'Bot {bid}: {r["result"][0]["name"]} - {len(ret_lines)} ret lines')
    
    # Check if code uses send_message_bus_release (direct send)
    uses_direct_send = 'send_message_bus_release' in code
    
    if uses_direct_send:
        # Just add ret = env['acrux.chat.bot'] at the end
        # First, remove existing ret lines
        new_lines = []
        for l in lines:
            stripped = l.strip()
            if stripped.startswith('ret =') and ('{\'send' in stripped or '{' in stripped):
                # Replace ret = [...] with ret = env['acrux.chat.bot']
                new_lines.append('ret = env[\'acrux.chat.bot\']')
            elif stripped.startswith('ret =') and stripped == 'ret = []':
                new_lines.append('ret = env[\'acrux.chat.bot\']')
            else:
                new_lines.append(l)
        new_code = '\n'.join(new_lines)
    else:
        # Doesn't use direct send - need to analyze more
        # For bots with ret = [{'send_text':...}], convert to direct send
        print(f'  No direct send - need full rewrite')
        continue
    
    try:
        compile(new_code, '<string>', 'exec')
        resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[bid], {'code': new_code}], 'kwargs': {}
            }
        })
        if resp2.json().get('result'):
            print(f'  ✅ Fixed')
        else:
            print(f'  ❌ Error: {resp2.json().get("error",{}).get("message","")[:80]}')
    except SyntaxError as e:
        print(f'  ❌ Syntax error: {e}')
