from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Get ALL bots
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[]],
        'kwargs': {'fields': ['id', 'name', 'active', 'connector_id'],
            'order': 'id'}
    }
})
bots = resp.json().get('result', [])

print(f"Total bots: {len(bots)}")

# Check for remaining ret = [...] with send_text patterns
print("\n--- Bots with 'ret = [{' pattern ---")
found_any = False
for b in bots:
    if not b.get('code'):
        continue
    if "ret = [{'send_text" in b['code'] or 'ret = [{"send_text' in b['code']:
        print(f"  Bot {b['id']:>3}: {b['name'][:40]:<40} (ACTIVE={b['active']})")
        found_any = True
        # Show the exact line
        for line in b['code'].split('\n'):
            if 'ret = [{' in line:
                print(f"       {line.strip()[:120]}")
    elif "ret = [{'goto_and_wait" in b['code'] or 'ret = [{"goto_and_wait' in b['code']:
        print(f"  Bot {b['id']:>3}: {b['name'][:40]:<40} (ACTIVE={b['active']}) - has goto_and_wait")
        found_any = True
        for line in b['code'].split('\n'):
            if 'ret = [{' in line:
                print(f"       {line.strip()[:120]}")

if not found_any:
    print("  ✓ None found - all clean!")

# Also check for multi-line ret
print("\n--- Bots with 'ret = [' (empty or multi-line) ---")
for b in bots:
    if not b.get('code'):
        continue
    lines = b['code'].split('\n')
    for line in lines:
        sline = line.strip()
        if sline == 'ret = []' or sline == 'ret = [':
            print(f"  Bot {b['id']:>3}: {b['name'][:40]:<40} -> {sline}")
            break

# Check bots that still have multi-line ret patterns (not already caught)
print("\n--- Bots with 'ret = env' (our fixed pattern) ---")
for b in bots:
    if b.get('code') and "ret = env" in b['code']:
        print(f"  Bot {b['id']:>3}: {b['name'][:40]:<40} ✓")
