import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[]],
        'kwargs': {'fields': ['id', 'name', 'active', 'code'],
            'order': 'id'}
    }
})
bots = resp.json().get('result', [])

print(f"Total bots: {len(bots)}")

# Check for remaining ret = [ patterns (excluding ret = env[...])
problematic = []
for b in bots:
    code = b.get('code') or ''
    if not code.strip():
        continue
    
    # Check if code has any ret = [ with send_text or goto_and_wait
    has_problem = False
    for line in code.split('\n'):
        sline = line.strip()
        # Skip ret = env[...] and ret = self.env[...]
        if 'ret = env[' in sline or 'ret = self.env[' in sline:
            continue
        # Check for ret = [{'send_text' or ret = [{'goto_and_wait'
        if sline.startswith("ret = [{'send_") or sline.startswith("ret = [{'goto_") or sline.startswith('ret = [{"send_') or sline.startswith('ret = [{"goto_'):
            has_problem = True
            break
        # Check for multiline ret = [ on its own
        if sline == 'ret = [':
            has_problem = True
            break
    
    if has_problem:
        problematic.append(b)
        print(f'\n❌ Bot {b["id"]} ({b["name"]}):')
        for line in code.split('\n'):
            sline = line.strip()
            if sline.startswith('ret') or 'ret = [' in sline:
                print(f'    {line.strip()[:150]}')

if not problematic:
    print("\n✅ ALL CLEAN! No problematic 'ret = [' patterns found.")
else:
    print(f"\n⚠️  {len(problematic)} bots still have problematic patterns")
