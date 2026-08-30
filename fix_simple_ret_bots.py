import requests, json, re, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read ALL bot codes to find simple 1-line ret bots
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'code', 'text_match', 'active', 'parent_id', 'connector_id'],
            'domain': [['active', 'in', [True, False]]],
            'limit': 200
        }
    }
})
r = resp.json()
if 'result' not in r:
    print('Error')
    exit()

records = r['result']
if isinstance(records, dict):
    records = records.get('records', [])

# Bots that have simple ret = [{'send_text': '...'}] pattern (1 line, no goto_and_wait)
simple_sendtext_bots = []  # (id, name, text_match, code)
complex_bots = []
already_fixed = [58, 62]  # Already fixed

for bot in records:
    bid = bot['id']
    code = bot.get('code') or ''
    if bid in already_fixed:
        continue
    if not code.strip():
        continue
    
    lines = code.strip().split('\n')
    if len(lines) <= 3:  # Simple bots have 1-3 lines
        # Check if it's just ret = [{'send_text': '...'}]
        stripped = code.strip()
        if stripped.startswith('ret = [{\'send_text\''):
            simple_sendtext_bots.append((bid, bot['name'], bot.get('text_match',''), code))
            continue
        if stripped.startswith('ret = [{"send_text"'):
            simple_sendtext_bots.append((bid, bot['name'], bot.get('text_match',''), code))
            continue
        if stripped.startswith('ret = [{' + "'send_text'"):
            simple_sendtext_bots.append((bid, bot['name'], bot.get('text_match',''), code))
            continue

# Keep only bots with connector=2 (commercial) or that are active
print(f'Simple bots to fix (just send_text): {len(simple_sendtext_bots)}')
for bid, name, tm, code in sorted(simple_sendtext_bots):
    print(f'  Bot {bid}: {name} [text_match={tm}]')
print()

# Fix each simple bot
fixed = []
for bid, name, tm, code in simple_sendtext_bots:
    # Extract the text from the ret statement
    # Pattern: ret = [{'send_text': 'TEXT'}] or ret = [{"send_text": "TEXT"}]
    match = re.search(r"'send_text':\s*'([^']*)'", code)
    if not match:
        match = re.search(r'"send_text":\s*"([^"]*)"', code)
    
    if not match:
        print(f'  Could not extract text from bot {bid}: {name}')
        continue
    
    text = match.group(1)
    # Escape special chars for Python string
    text_escaped = text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    
    new_code = f"""conv = mess_id.conversation_id
msg_data = {{'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': '{text_escaped}'}}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""
    
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        fixed.append(bid)
        print(f'  ✅ Bot {bid}: {name}')
    else:
        print(f'  ❌ Bot {bid}: {name} - {resp2.json().get("error",{}).get("message","")[:80]}')

print()
print(f'✅ {len(fixed)} bots arreglados')
