import requests, json, sys, re
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get ALL bots including code field
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[]],
        'kwargs': {'fields': ['id', 'name', 'active', 'connector_id', 'parent_id', 'code'],
            'order': 'id'}
    }
})
bots = resp.json().get('result', [])

print(f"Total bots: {len(bots)}")
print()

# Check for remaining ret = [...] patterns
print("=== Bots with problematic 'ret = [' patterns ===")
for b in bots:
    code = b.get('code') or ''
    if not code.strip():
        continue
    
    # Check for ret = [{'send_text' or ret = [{'goto_and_wait'
    if "ret = [{'send_" in code or 'ret = [{"send_' in code:
        print(f"\n❌ Bot {b['id']} ({b['name']}):")
        for line in code.split('\n'):
            if 'ret = [{' in line:
                print(f"    {line.strip()[:150]}")
    elif "ret = [{'goto_" in code or 'ret = [{"goto_' in code:
        print(f"\n❌ Bot {b['id']} ({b['name']}): has ret = [{{'goto_")
        for line in code.split('\n'):
            if 'ret = [{' in line:
                print(f"    {line.strip()[:150]}")
    elif "ret = [" in code and 'env[' not in code:
        # Check for ret = [] or ret = [ on its own line
        lines = code.split('\n')
        for line in lines:
            sline = line.strip()
            if sline == 'ret = []':
                print(f"\n⚠️  Bot {b['id']} ({b['name']}): has 'ret = []'")
        # Also check for multi-line ret = [ ... ]
        if 'ret = [' in code and 'ret = env' not in code and 'ret = [{' not in code:
            # Could be multi-line
            for line in lines:
                if 'ret = [' in line and 'env' not in line:
                    print(f"\n⚠️  Bot {b['id']} ({b['name']}): line '{line.strip()[:100]}'")

print("\n=== Bots with 'ret = env' (correctly fixed) ===")
fixed = 0
for b in bots:
    code = b.get('code') or ''
    if "ret = env" in code:
        print(f"  ✓ Bot {b['id']:>3}: {b['name'][:40]}")
        fixed += 1
print(f"Total fixed: {fixed}")
