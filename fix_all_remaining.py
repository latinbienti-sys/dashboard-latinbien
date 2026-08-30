import requests, json, sys, re
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

def read_bot(bid):
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code', 'connector_id', 'parent_id']}
        }
    })
    r = resp.json()
    return r['result'][0] if 'result' in r and r['result'] else None

def write_bot(bid, code):
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], {'code': code}], 'kwargs': {}
        }
    })
    return resp.json().get('result', False)

def replace_ret_simple(text, indent, var_expr, suffix=''):
    """Replace 'ret = [{'send_text': var_expr}]' with direct send code"""
    lines = []
    send_expr = f'{var_expr}{suffix}' if suffix else var_expr
    lines.append(f'{indent}conv = mess_id.conversation_id')
    lines.append(f'{indent}msg_data = {{\'ttype\': \'text\', \'from_me\': True, \'contact_id\': conv.id, \'text\': {send_expr}}}')
    lines.append(f'{indent}back = conv.status')
    lines.append(f'{indent}if back == \'current\':')
    lines.append(f'{indent}    conv.send_message_bus_release(msg_data, \'current\', False)')
    lines.append(f'{indent}else:')
    lines.append(f'{indent}    conv.block_conversation()')
    lines.append(f'{indent}    conv.send_message_bus_release(msg_data, \'done\')')
    lines.append(f'{indent}ret = env[\'acrux.chat.bot\']')
    return '\n'.join(lines)

def replace_ret_goto(text, indent, var_expr, target_name):
    """Replace ret with goto_and_wait"""
    lines = []
    # Escape single quotes in target name
    target_esc = target_name.replace("'", "\\'")
    lines.append(f'{indent}conv = mess_id.conversation_id')
    lines.append(f'{indent}target = env[\'acrux.chat.bot\'].search([(\'name\', \'ilike\', \'%{target_esc}%\')], limit=1)')
    lines.append(f'{indent}if target:')
    lines.append(f'{indent}    conv.write({{\'active_bot_id\': target.id}})')
    lines.append(f'{indent}msg_data = {{\'ttype\': \'text\', \'from_me\': True, \'contact_id\': conv.id, \'text\': {var_expr}}}')
    lines.append(f'{indent}back = conv.status')
    lines.append(f'{indent}if back == \'current\':')
    lines.append(f'{indent}    conv.send_message_bus_release(msg_data, \'current\', False)')
    lines.append(f'{indent}else:')
    lines.append(f'{indent}    conv.block_conversation()')
    lines.append(f'{indent}    conv.send_message_bus_release(msg_data, \'done\')')
    lines.append(f'{indent}ret = env[\'acrux.chat.bot\']')
    return '\n'.join(lines)

# === FIX BOTS 74, 85, 95 (CONVENIO) - replace the 2 remaining ret lines ===
for bid in [74, 85, 95]:
    bot = read_bot(bid)
    if not bot:
        continue
    code = bot['code']
    
    # Replace: '            ret = [{'send_text': msg}]'  (the if es_convenio branch)
    # This appears twice: once in if es_convenio: and once in else:
    old_ret = "            ret = [{'send_text': msg}]"
    new_code = replace_ret_simple(code, '            ', 'msg')
    
    if new_code == code:
        print(f"❌ Bot {bid}: pattern not found!")
        continue
    
    try:
        compile(new_code, '<string>', 'exec')
        if write_bot(bid, new_code):
            print(f'✅ Bot {bid}: {bot["name"]}')
        else:
            print(f'❌ Bot {bid}: write failed')
    except SyntaxError as e:
        print(f'❌ Bot {bid}: syntax error L{e.lineno}: {e.msg}')

# === FIX BOT 86 (EVALUAR CEDULA CONVENIO) ===
# Has multiple ret patterns with different variables
print()
bot86 = read_bot(86)
if bot86:
    code86 = bot86['code']
    
    # Replace 5 ret patterns one by one
    # 1. ret = [{'send_text': msg_convenio}]
    code86 = code86.replace(
        '            ret = [{\'send_text\': msg_convenio}]',
        replace_ret_simple(code86, '            ', 'msg_convenio')
    )
    
    # 2 & 3: goto_and_wait patterns (use search for target bot names)
    code86 = code86.replace(
        "                ret = [{'goto_and_wait': '#MENU_RECOMPRA', 'send_text': msg_no_conv}]",
        replace_ret_goto(code86, '                ', 'msg_no_conv', 'MENU_RECOMPRA')
    )
    
    # For '#No tienes linea' - search for the bot that handles this case
    code86 = code86.replace(
        "                ret = [{'goto_and_wait': '#No tienes linea', 'send_text': msg_no_conv}]",
        replace_ret_goto(code86, '                ', 'msg_no_conv', 'MENU_NO_REGISTRADO')
    )
    
    # 4 & 5: f-string patterns - use the f-string directly
    code86 = code86.replace(
        '        ret = [{\'send_text\': f"\\U0001f6d1 No encontr\\u00e9 ning\\u00fan cliente con la identificaci\\u00f3n num\\u00e9rica: *{cedula_numerica}*. Por favor, verifica el n\\u00famero o escribe *\\"ASESOR\\"."}]',
        replace_ret_simple(code86, '        ', 'f"\\U0001f6d1 No encontr\\u00e9 ning\\u00fan cliente con la identificaci\\u00f3n num\\u00e9rica: *{cedula_numerica}*. Por favor, verifica el n\\u00famero o escribe *\\"ASESOR\\"."')
    )
    
    code86 = code86.replace(
        '        ret = [{\'send_text\': f"\\U0001f6d1 *Error al validar convenio:* {str(e)}"}]',
        replace_ret_simple(code86, '        ', 'f"\\U0001f6d1 *Error al validar convenio:* {str(e)}"')
    )
    
    try:
        compile(code86, '<string>', 'exec')
        if write_bot(86, code86):
            print(f'✅ Bot 86: {bot86["name"]}')
        else:
            print(f'❌ Bot 86: write failed')
    except SyntaxError as e:
        print(f'❌ Bot 86: syntax error L{e.lineno}: {e.msg}')
        lines = code86.split('\n')
        for j in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
            print(f'  L{j+1}: {lines[j][:130]}')

# === FIX SEARCH BOTS 107, 108, 109, 117 ===
# Pattern: ret = [{'send_text': msg, 'goto_and_wait': '#...'}]
print()
goto_targets = {
    107: ('MENU_LC_APROBADA', 'MENU_LC_APROBADA'),
    108: ('No tienes linea', 'MENU_NO_REGISTRADO'),  # Fallback to MENU_REGISTRADO
    109: ('Registro', 'MENU_NO_REGISTRADO'),
    117: ('CATCHER CHATBOT (CONECTOR DE COMERCIAL)', 'CATCHER CHATBOT (CONECTOR DE COMERCIAL)'),
}

for bid, (goto_name, target_search) in goto_targets.items():
    bot = read_bot(bid)
    if not bot:
        continue
    code = bot['code']
    
    # The ret line is at the end: ret = [{'send_text': msg, 'goto_and_wait': '#...'}]
    # Find and replace it
    old = f"ret = [{{'send_text': msg, 'goto_and_wait': '#{goto_name}'}}]"
    if old not in code:
        print(f'⚠️  Bot {bid}: pattern not found, checking variant...')
        # Try reversed order
        old = f"ret = [{{'goto_and_wait': '#{goto_name}', 'send_text': msg}}]"
    
    if old in code:
        new = replace_ret_goto(code, '', 'msg', target_search)
        code = code.replace(old, new)
        
        try:
            compile(code, '<string>', 'exec')
            if write_bot(bid, code):
                print(f'✅ Bot {bid}: {bot["name"]}')
            else:
                print(f'❌ Bot {bid}: write failed')
        except SyntaxError as e:
            print(f'❌ Bot {bid}: syntax error L{e.lineno}: {e.msg}')
    else:
        print(f'❌ Bot {bid}: pattern still not found in code')

# === FIX SEARCH BOTS 122, 124, 125 ===
# Pattern: ret = [{'send_text': msg + MENU}]
print()
for bid in [122, 124, 125]:
    bot = read_bot(bid)
    if not bot:
        continue
    code = bot['code']
    
    old = "ret = [{'send_text': msg + MENU}]"
    if old in code:
        new = replace_ret_simple(code, '', 'msg + MENU')
        code = code.replace(old, new)
        
        try:
            compile(code, '<string>', 'exec')
            if write_bot(bid, code):
                print(f'✅ Bot {bid}: {bot["name"]}')
            else:
                print(f'❌ Bot {bid}: write failed')
        except SyntaxError as e:
            print(f'❌ Bot {bid}: syntax error L{e.lineno}: {e.msg}')
    else:
        print(f'⚠️  Bot {bid}: pattern not found')

# === FIX COBRANZA BOTS 40, 41 ===
# These have multi-line ret with goto_and_wait: '#CATCHER'
print()
for bid in [40, 41]:
    bot = read_bot(bid)
    if not bot:
        continue
    code = bot['code']
    
    # Find the multiline ret block
    # Bot 40 has:
    #   ret = [{'goto_and_wait': '#CATCHER',
    #     'send_text': f"""...""" 
    # }]
    # Bot 41 has:
    #   ret = [{'goto_and_wait': '#CATCHER', 'send_text': texto}]
    
    # Find 'ret = [{' and its matching '}]'
    start = code.find("ret = [{'")
    if start >= 0:
        # Find the matching '}]'
        end = code.find('}]', start) + 2
        old = code[start:end]
        
        # Extract the text expression
        if 'f"""' in old:
            text_expr = 'f"""' + old.split('f"""')[1].split('"""')[0] + '"""'
        elif "'send_text': texto" in old:
            text_expr = 'texto'
        elif "'send_text': f" in old:
            text_expr = old.split("'send_text': ")[1].rsplit('}', 1)[0].strip()
        else:
            text_expr = "msg"
        
        new = replace_ret_goto(code, code[:len(code) - len(code.lstrip())], text_expr, 'CATCHER')
        code = code.replace(old, new)
        
        try:
            compile(code, '<string>', 'exec')
            if write_bot(bid, code):
                print(f'✅ Bot {bid}: {bot["name"]}')
            else:
                print(f'❌ Bot {bid}: write failed')
        except SyntaxError as e:
            print(f'❌ Bot {bid}: syntax error L{e.lineno}: {e.msg}')
            lines = code.split('\n')
            for j in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
                print(f'  L{j+1}: {lines[j][:130]}')
