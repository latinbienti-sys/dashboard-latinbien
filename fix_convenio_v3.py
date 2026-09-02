import requests, json, sys, re
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

def fix_ret_with_indent(code):
    """Replace ret = [...] with properly indented direct send"""
    lines = code.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if line is ret = [something]
        if stripped.startswith('ret = [{\'send_text') or stripped.startswith('ret = [{"send_text'):
            # Get indentation
            indent = line[:len(line) - len(line.lstrip())]
            
            # Extract text
            text_match = re.search(r"'send_text':\s*'([^']*)'", stripped)
            if not text_match:
                text_match = re.search(r'"send_text":\s*"([^"]*)"', stripped)
            
            if text_match:
                text = text_match.group(1)
                text_escaped = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
                
                # Check for goto_and_wait
                if 'goto_and_wait' in stripped:
                    goto_match = re.search(r"'goto_and_wait':\s*'#?([^']*)'", stripped)
                    if goto_match:
                        goto_name = goto_match.group(1)
                        target_id = 0
                        if 'RECOMPRA' in goto_name:
                            target_id = 65
                        elif 'LC' in goto_name or 'LC_' in goto_name:
                            target_id = 66
                        elif 'REG' in goto_name:
                            target_id = 64
                        elif 'No tienes' in goto_name:
                            target_id = 64  # Fallback to MENU_REGISTRADO
                        
                        if target_id:
                            new_lines.append(f'{indent}conv = mess_id.conversation_id')
                            new_lines.append(f'{indent}target = env[\'acrux.chat.bot\'].browse({target_id})')
                            new_lines.append(f'{indent}if target:')
                            new_lines.append(f'{indent}    conv.write({{\'active_bot_id\': target.id}})')
                            new_lines.append(f'{indent}msg_data = {{\'ttype\': \'text\', \'from_me\': True, \'contact_id\': conv.id, \'text\': \'{text_escaped}\'}}')
                            new_lines.append(f'{indent}back = conv.status')
                            new_lines.append(f'{indent}if back == \'current\':')
                            new_lines.append(f'{indent}    conv.send_message_bus_release(msg_data, \'current\', False)')
                            new_lines.append(f'{indent}else:')
                            new_lines.append(f'{indent}    conv.block_conversation()')
                            new_lines.append(f'{indent}    conv.send_message_bus_release(msg_data, \'done\')')
                            new_lines.append(f'{indent}ret = env[\'acrux.chat.bot\']')
                        else:
                            new_lines.append(line)  # Keep original
                    else:
                        new_lines.append(line)  # Keep original
                else:
                    # Simple send_text
                    new_lines.append(f'{indent}conv = mess_id.conversation_id')
                    new_lines.append(f'{indent}msg_data = {{\'ttype\': \'text\', \'from_me\': True, \'contact_id\': conv.id, \'text\': \'{text_escaped}\'}}')
                    new_lines.append(f'{indent}back = conv.status')
                    new_lines.append(f'{indent}if back == \'current\':')
                    new_lines.append(f'{indent}    conv.send_message_bus_release(msg_data, \'current\', False)')
                    new_lines.append(f'{indent}else:')
                    new_lines.append(f'{indent}    conv.block_conversation()')
                    new_lines.append(f'{indent}    conv.send_message_bus_release(msg_data, \'done\')')
                    new_lines.append(f'{indent}ret = env[\'acrux.chat.bot\']')
            else:
                new_lines.append(line)  # Keep original if can't parse
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

# Fix all convenio bots
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
    name = r['result'][0]['name']
    
    new_code = fix_ret_with_indent(code)
    
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
        print(f'❌ Bot {bid}: {name} - Syntax error at line {e.lineno}: {e.msg}')
        # Show the problematic area
        lines = new_code.split('\n')
        for j in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
            print(f'  L{j+1}: {lines[j][:120]}')
