import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Read bot 62 code
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# Find where the menu starts (first if texto)
idx_if = code.find('\nif texto ==')
if idx_if >= 0:
    # Split code into:
    # Line 1: texto = (mess_id.text or '').strip()
    # Line 2: (blank)
    # Line 3: # ========== MENU OPTIONS (1-6) ==========
    # Line 4+: if texto == '6': ...
    # etc.
    
    # The header is everything before the first 'if'
    header = code[:idx_if]  # texto = ...\n\n# ========== ... ==========
    
    # The menu body is everything from 'if texto ==' onwards
    body = code[idx_if:]  # if texto == '6':\n    ret = ...
    
    # Get the indentation of the first 'if'
    indent = ''
    for ch in body:
        if ch == ' ':
            indent += ch
        else:
            break
    
    # Add indentation to each line of the body (add 4 spaces)
    indented_body = ''
    for line in body.split('\n'):
        if line.strip():  # non-empty
            indented_body += '    ' + line + '\n'
        else:  # empty line
            indented_body += '\n'
    
    # New complete code
    new_code = header + '\n\n# Check for non-text messages (documents, images, etc.)\ntry:\n    ttype = mess_id.ttype or \'text\'\nexcept:\n    ttype = \'text\'\n\nif ttype != \'text\':\n    ret = [{\'send_text\': \'Recib\u00ed tu archivo pero solo proceso mensajes de texto. Por favor escribe tu c\u00e9dula o el n\u00famero de la opci\u00f3n deseada.\'}]\nelif not texto:\n    ret = [{\'send_text\': \'No entend\u00ed tu mensaje. Por favor escribe tu n\u00famero de c\u00e9dula o selecciona una opci\u00f3n del men\u00fa.\'}]\nelse:\n' + indented_body
    
    # Verify syntax
    try:
        compile(new_code, '<string>', 'exec')
        print('Syntax OK')
    except SyntaxError as e:
        print(f'Syntax error at line {e.lineno}: {e.msg}')
        lines2 = new_code.split('\n')
        for i in range(max(0, e.lineno-5), min(len(lines2), e.lineno+3)):
            print(f'  {i+1}: {lines2[i]}')
        exit()
    
    # Write
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - Bot 62 updated')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('if texto == not found')
    print(code[:200])
