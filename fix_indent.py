import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']
lines = code.split('\n')

# Find the else: line
else_idx = None
for i, line in enumerate(lines):
    if line.strip() == 'else:':
        else_idx = i
        break

if else_idx is None:
    print('else: not found')
    exit()

print(f'else: found at line {else_idx+1}')

# Check indentation of first line inside else
if else_idx + 1 < len(lines):
    first_line = lines[else_idx + 1]
    print(f'First line after else: indentation = {len(first_line) - len(first_line.lstrip())}')
    print(f'  Content: {repr(first_line)}')

# Fix: re-indent all lines after else: from 8->4, 12->8, etc.
# Current pattern: 8 spaces for first level inside else, 12 for second, etc.
# Target: 4 spaces for first level, 8 for second, etc.
fixed = False
for i in range(else_idx + 1, len(lines)):
    stripped = lines[i]
    if stripped.strip() == '':
        continue  # skip empty lines
    indent = len(stripped) - len(stripped.lstrip())
    if indent >= 8:
        # Reduce by 4 spaces
        new_indent = indent - 4
        lines[i] = ' ' * new_indent + stripped.lstrip()
        fixed = True

if not fixed:
    print('No lines needed fixing (already correct)')
else:
    new_code = '\n'.join(lines)
    
    # Verify syntax
    try:
        compile(new_code, '<string>', 'exec')
        print('Syntax OK after fix')
    except SyntaxError as e:
        print(f'Syntax error at line {e.lineno}: {e.msg}')
        for j in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
            print(f'  L{j+1}: {repr(lines[j])}')
        exit()
    
    # Show before/after
    print()
    print('=== Fixed lines (first 20) ===')
    for j in range(max(0, else_idx - 1), min(len(lines), else_idx + 20)):
        print(f'  L{j+1}: |{lines[j]}|')
    
    # Write
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - Indentation fixed')
    else:
        print('ERROR:', resp2.json().get('error', {}))
