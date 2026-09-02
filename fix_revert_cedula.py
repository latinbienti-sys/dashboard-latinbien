import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Read current code
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# Remove the len/texto block (DEBUG) - it's between the first line and "elif texto == '6':"
old_block = ('if len(texto) > 1 and texto[0] == \'6\':\n'
             '    query = texto[1:].strip()\n'
             '    ret = [{\'send_text\': \'DEBUG: texto=\' + repr(texto) + \' | query=\' + repr(query) + \' | len=\' + str(len(query))}]\n'
             'elif texto == \'6\':\n'
             '    ret = [{\'send_text\': \'Escribe 6 seguido del nombre del producto, ej: 6 televisor\'}]\n')

new_block = ('if texto == \'6\':\n'
             '    ret = [{\'send_text\': \'Escribe 6 seguido del nombre del producto, ej: 6 televisor\'}]\n')

if old_block in code:
    new_code = code.replace(old_block, new_block, 1)
else:
    print('old block not found exactly. Trying partial match...')
    # Find where the len block is
    idx = code.find('len(texto)')
    if idx >= 0:
        # Remove from that line to before "elif texto:"
        start = code.rfind('\n', 0, idx)  # go back to previous newline
        end = code.find('\nelif texto:', idx)
        if start >= 0 and end > start:
            # Extract what's between
            to_remove = code[start:end]  # includes the \n before and after
            print('Removing:', repr(to_remove[:100]))
            # Keep the elif texto: part
            new_code = code[:start] + '\n' + code[end:]
        else:
            print('Could not find boundaries')
            print('idx:', idx, 'start:', start, 'end:', end)
            new_code = code
    else:
        # Maybe DEBUG is not in the code anymore
        print('len(texto) not found in code')
        print('First 300 chars:', repr(code[:300]))
        new_code = code

# Verify the replacement
if 'len(texto)' in new_code:
    print('WARNING: len(texto) still present after replacement')
else:
    print('OK - len(texto) removed')

# Write
resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[62], {'code': new_code}], 'kwargs': {}
    }
})
if resp2.json().get('result'):
    print('OK - VALIDAR_CEDULA written')
else:
    print('ERROR:', resp2.json().get('error', {}))
