import requests, json, sys, re
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Helper: map goto names to bot IDs
GOTO_IDS = {
    'MENU_RECOMPRA': 65,
    'MENU_LC_APROBADA': 66,
    'MENU_REGISTRADO': 64,
}

def fix_ret_code(code, bot_id=None):
    """Replace ret = [...] with direct send + ret = env['acrux.chat.bot']"""
    lines = code.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if this line starts ret = [
        if stripped.startswith('ret = ['):
            # Collect all lines of the ret statement
            ret_text = ''
            j = i
            bracket_count = stripped.count('[') - stripped.count(']')
            while j < len(lines):
                ret_text += lines[j] + '\n'
                bracket_count += lines[j].count('[') - lines[j].count(']')
                j += 1
                if bracket_count <= 0 and j > i + 1:
                    break
                if bracket_count <= 0 and j == i + 1:
                    # Single line
                    if ']' in lines[j-1]:
                        break
            else:
                j = i + 1  # fallback
            
            # Parse the ret block
            ret_block = ret_text.strip()
            
            # Check for goto_and_wait
            goto_match = re.search(r"'goto_and_wait':\s*'#?([^']*)'", ret_block)
            
            # Extract send_text
            text_match = re.search(r"'send_text':\s*'([^']*)'", ret_block)
            if not text_match:
                text_match = re.search(r'"send_text":\s*"([^"]*)"', ret_block)
            if not text_match:
                text_match = re.search(r"'send_text':\s*f[\"']([^\"']*)[\"']", ret_block)
            
            if text_match:
                text = text_match.group(1)
                text_escaped = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
                
                if goto_match:
                    goto_name = goto_match.group(1)
                    target_id = GOTO_IDS.get(goto_name, False)
                    if not target_id:
                        # Search by name
                        target_id = f"env['acrux.chat.bot'].search([('name','ilike','%{goto_name}%')],limit=1)"
                    
                    new_lines.append(f"""conv = mess_id.conversation_id
if {target_id}:
    conv.write({{'active_bot_id': {target_id}.id}})
msg_data = {{'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': '{text_escaped}'}}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']""")
                else:
                    new_lines.append(f"""conv = mess_id.conversation_id
msg_data = {{'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': '{text_escaped}'}}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']""")
            else:
                # Could not parse - keep original
                for k in range(i, j):
                    new_lines.append(lines[k])
            
            i = j
        else:
            new_lines.append(line)
            i += 1
    
    return '\n'.join(new_lines)

# Fix convenio bots
for bid in [85, 74, 95]:
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
    name = r['result'][0]['name']
    
    new_code = fix_ret_code(code, bid)
    
    try:
        compile(new_code, '<string>', 'exec')
        resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[bid], {'code': new_code}], 'kwargs': {}
            }
        })
        print(f'✅ Bot {bid}: {name}' if resp2.json().get('result') else f'❌ Bot {bid}: error')
    except SyntaxError as e:
        print(f'❌ Bot {bid}: {name} - Syntax error: {e}')

# Fix bot 86 (EVALUAR CEDULA CONVENIO) - more complex
print()
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[86]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
r = resp.json()
if 'result' in r and r['result']:
    code86 = r['result'][0].get('code', '')
    name86 = r['result'][0]['name']
    
    new_code86 = fix_ret_code(code86, 86)
    
    try:
        compile(new_code86, '<string>', 'exec')
        resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[86], {'code': new_code86}], 'kwargs': {}
            }
        })
        print(f'✅ Bot 86: {name86}' if resp2.json().get('result') else f'❌ Bot 86: error')
    except SyntaxError as e:
        print(f'❌ Bot 86: {name86} - Syntax error: {e}')
