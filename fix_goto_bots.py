import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Map of #NAME to actual bot ID for navigation
GOTO_MAP = {
    '#RECOMPRA_BUSCAR': 106,
    '#LC_BUSCAR': 107,
    '#REG_BUSCAR': 108,
    '#NR_BUSCAR': 109,
}

# Bot codes that were lost: goto_and_wait + clear_catcher
# Read full current codes
bots_to_fix = [83, 94, 102, 103, 104, 105]

for bid in bots_to_fix:
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
    bot = r['result'][0]
    code = bot.get('code', '')
    print(f'Bot {bid} ({bot["name"]}): código actual = "{code[:100]}..."')
    
    # Extract text from current code
    import re
    match = re.search(r"'text':\s*'([^']*)'", code)
    if not match:
        print(f'  Cannot extract text')
        continue
    
    text = match.group(1)
    print(f'  Text: {text[:60]}...')
    
    # Determine the new code based on original functionality
    if bid == 83:  # NR_PROBLEMA - clear_catcher
        new_code = f"""conv = mess_id.conversation_id
conv.write({{'active_bot_id': False}})
msg_data = {{'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': '{text}'}}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""
    else:  # goto_and_wait bots
        # Determine goto target from bot ID
        goto_targets = {
            94: '#NR_BUSCAR',
            102: '#RECOMPRA_BUSCAR',
            103: '#LC_BUSCAR',
            104: '#REG_BUSCAR',
            105: '#NR_BUSCAR',
        }
        goto_name = goto_targets.get(bid, '').lstrip('#')
        target_id = GOTO_MAP.get('#' + goto_name, False)
        
        if target_id:
            new_code = f"""conv = mess_id.conversation_id
target = env['acrux.chat.bot'].browse({target_id})
if target:
    conv.write({{'active_bot_id': target.id}})
msg_data = {{'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': '{text}'}}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""
        else:
            new_code = f"""conv = mess_id.conversation_id
msg_data = {{'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': '{text}'}}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""
    
    try:
        compile(new_code, '<string>', 'exec')
        resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[bid], {'code': new_code}], 'kwargs': {}
            }
        })
        if resp2.json().get('result'):
            print(f'  ✅ Bot {bid} corregido con navegación')
        else:
            print(f'  ❌ Error: {resp2.json().get("error",{}).get("message","")[:80]}')
    except SyntaxError as e:
        print(f'  ❌ Syntax error: {e}')
    print()
