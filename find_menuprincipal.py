import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get ALL bots and check their labels
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'code', 'text_match', 'parent_id'],
            'domain': [],
            'order': 'id asc'
        }
    }
})
r = resp.json()['result']
bots = r.get('records', r) if isinstance(r, dict) else r

# Search the code for labels (labels are defined in code as comment or in goto_and_wait)
print('=== Bots that use #MENUPRINCIPAL ===')
for b in bots:
    code = b.get('code', '') or ''
    if '#MENUPRINCIPAL' in code:
        print(f'  ID {b["id"]}: {b["name"]}')
        # Show the line
        for line in code.split('\n'):
            if '#MENUPRINCIPAL' in line:
                print(f'    -> {line.strip()}')

print()

# Check which bots have labels defined
print('=== Bots with label field ===')
for b in bots:
    code = b.get('code', '') or ''
    # Labels can be defined as a comment at the top
    lines = code.strip().split('\n')
    if lines and lines[0].startswith('# LABEL'):
        print(f'  ID {b["id"]}: {b["name"]} -> {lines[0]}')
    # Also check if code has '#MENU' or '#MENUPRINCIPAL' defined
    if code.strip().startswith('#') and 'MENU' in code.split('\n')[0].upper():
        print(f'  ID {b["id"]}: {b["name"]} -> {code.split(chr(10))[0]}')
