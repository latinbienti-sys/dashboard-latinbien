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

lines = code.split('\n')

# The header is: texto = (mess_id.text or '').strip()
# Then blank line
# Then "# ========== MENU OPTIONS..."
# Then if/elif chain

# Find the line with "# ========== MENU OPTIONS"
menu_comment_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith('# ======') and 'MENU OPTIONS' in line:
        menu_comment_idx = i
        break

if menu_comment_idx is None:
    print("Could not find MENU OPTIONS comment")
    exit()

# Get the first line (texto = ...)
header = lines[0]  # texto = (mess_id.text or '').strip()

# Everything from the comment onwards is the menu body
body_lines = lines[menu_comment_idx:]

# Indent every non-empty line of the body by 4 spaces
indented_body = ''
for line in body_lines:
    if line.strip():
        indented_body += '    ' + line + '\n'
    else:
        indented_body += '\n'

# Build new code
new_code = header + '\n\n# ========== DETECT NON-TEXT MESSAGES ==========\n'
new_code += "try:\n    ttype = mess_id.ttype or 'text'\nexcept:\n    ttype = 'text'\n\n"
new_code += "if ttype != 'text':\n"
new_code += "    ret = [{'send_text': 'Recib\u00ed tu archivo pero solo proceso mensajes de texto. Por favor escribe tu c\u00e9dula o el n\u00famero de la opci\u00f3n deseada.'}]\n"
new_code += "elif not texto:\n"
new_code += "    ret = [{'send_text': 'No entend\u00ed tu mensaje. Por favor escribe tu n\u00famero de c\u00e9dula o selecciona una opci\u00f3n del men\u00fa.'}]\n"
new_code += "else:\n"
new_code += indented_body

# Verify syntax
try:
    compile(new_code, '<string>', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error at line {e.lineno}: {e.msg}')
    print('--- Around error ---')
    lines2 = new_code.split('\n')
    for i in range(max(0, e.lineno-5), min(len(lines2), e.lineno+3)):
        print(f'  {i+1}: {lines2[i]}')
    exit()

# Show the first 20 lines for verification
print('=== First 20 lines of new code ===')
for i in range(min(20, len(new_code.split('\n')))):
    print(f'  {i+1}: {new_code.split(chr(10))[i]}')

print()
print('=== Last 10 lines of new code ===')
new_lines = new_code.split('\n')
for i in range(max(0, len(new_lines)-10), len(new_lines)):
    print(f'  {i+1}: {new_lines[i]}')

# Write
print()
confirm = input('Write to bot 62? (y/n): ')
if confirm.lower() == 'y':
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
    print('Cancelled')
