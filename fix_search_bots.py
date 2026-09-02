import requests, json, sys, re
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read full codes of search bots (107,108,109,122,124,125) and busqueda (117)
# and replace ret = [{'send_text': ...}] with direct send + ret = env['acrux.chat.bot']

search_bots = [107, 108, 109, 117, 122, 124, 125]

for bid in search_bots:
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
    
    # Strategy: find each ret = [{'send_text': '...'}] or ret = [{'send_text': f"...}]
    # and replace with direct send
    lines = code.split('\n')
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if line starts ret = [{'send_text': or ret = [{"send_text":
        if (stripped.startswith("ret = [{'send_text'") or 
            stripped.startswith('ret = [{"send_text"') or
            stripped.startswith("ret = [{'send_text': f")):
            
            # Extract the text from ret line(s)
            # Collect all lines of the ret statement
            ret_lines = [line]
            j = i + 1
            while j < len(lines):
                ret_lines.append(lines[j])
                if '}]' in lines[j] or '}]\n' in lines[j]:
                    j += 1
                    break
                j += 1
            
            ret_block = '\n'.join(ret_lines)
            
            # Extract the text between send_text quotes
            m = re.search(r"'send_text':\s*'([^']*(?:'[^']*)*)'", ret_block, re.DOTALL)
            if not m:
                m = re.search(r'"send_text":\s*"([^"]*(?:"[^"]*)*)"', ret_block, re.DOTALL)
            if not m:
                m = re.search(r"'send_text':\s*f[\"']([^\"']*(?:\"[\"'][^\"']*)*)[\"']", ret_block, re.DOTALL)
            
            if m:
                text = m.group(1)
                # Escape for Python string
                text_escaped = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
                
                new_lines.append(f"""conv = mess_id.conversation_id
msg_data = {{'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': '{text_escaped}'}}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']""")
                i = j
                continue
            else:
                # Could not parse - keep original
                new_lines.append(line)
        else:
            new_lines.append(line)
        
        i += 1
    
    new_code = '\n'.join(new_lines)
    
    try:
        compile(new_code, '<string>', 'exec')
        resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[bid], {'code': new_code}], 'kwargs': {}
            }
        })
        if resp2.json().get('result'):
            print(f'✅ Bot {bid}: {name} fixed')
        else:
            print(f'❌ Bot {bid}: {name} - {resp2.json().get("error",{}).get("message","")[:80]}')
    except SyntaxError as e:
        print(f'❌ Bot {bid}: {name} - Syntax error: {e}')
