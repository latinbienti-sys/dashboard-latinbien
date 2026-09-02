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

# Find the exact lines to modify
lines = code.split('\n')

# 1. Add non-text detection AFTER 'texto = ...' line (line 1-2)
# Current: 
#   texto = (mess_id.text or '').strip()
#   (blank line)
#   # ========== MENU OPTIONS (1-6) ==========
#   if texto == '6':
#
# New:
#   texto = (mess_id.text or '').strip()
#   ttype = mess_id.ttype if hasattr(mess_id, 'ttype') else 'text'
#   if ttype != 'text':
#       ret = [{'send_text': 'Recib\u00ed tu archivo pero solo proceso mensajes de texto. Por favor escribe tu c\u00e9dula o una opci\u00f3n del men\u00fa.'}]
#   elif not texto:
#       ret = [{'send_text': 'No entend\u00ed tu mensaje. Por favor escribe el n\u00famero de la opci\u00f3n deseada o tu n\u00famero de c\u00e9dula para identificarte.'}]
#   else:
#       [existing code indented one level]

# Find the position of the first 'if' (the menu section starts)
# The structure is:
#   texto = (...).strip()
#   (blank)
#   # ========== MENU OPTIONS (1-6) ==========
#   if texto == '6':
first_if_idx = None
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('if texto'):
        first_if_idx = i
        break

if first_if_idx is not None:
    print(f'Found if at line {first_if_idx+1}')
    
    # Everything from first_if to end needs to be indented under 'else:'
    rest_code = '\n'.join(lines[first_if_idx:])
    indent = lines[first_if_idx][:len(lines[first_if_idx]) - len(lines[first_if_idx].lstrip())]
    
    # Add the non-text and empty-text checks
    checks = f'''ttype = ''
try:
    ttype = mess_id.ttype or 'text'
except:
    ttype = 'text'
if ttype != 'text':
    ret = [{{'send_text': 'Recib\u00ed tu archivo pero solo proceso mensajes de texto. Por favor escribe tu c\u00e9dula o una opci\u00f3n del men\u00fa.'}}]
elif not texto:
    ret = [{{'send_text': 'No entend\u00ed tu mensaje. Por favor escribe el n\u00famero de la opci\u00f3n deseada o tu n\u00famero de c\u00e9dula para identificarte.'}}]
else:
{rest_code}'''
    
    # Reconstruct the code
    first_part = '\n'.join(lines[:first_if_idx])
    new_code = first_part + '\n' + checks
    
    # Verify syntax
    try:
        compile(new_code, '<string>', 'exec')
        print('Syntax OK')
    except SyntaxError as e:
        print(f'Syntax error: {e}')
        lines2 = new_code.split('\n')
        for i in range(max(0, e.lineno-3), min(len(lines2), e.lineno+3)):
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
        print('OK - Bot 62 updated with file detection and fallback')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('First if not found')
    print(f'Lines 0-5:')
    for i in range(min(6, len(lines))):
        print(f'  {i+1}: {repr(lines[i])}')
