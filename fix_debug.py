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

# Add debug: after getting texto, send it back
# We'll replace the current 6 handler with a debug version that shows texto and query
old = ("if len(texto) > 1 and texto[0] == '6':\n"
       "    query = texto[1:].strip()\n"
       "    if query:\n"
       "        Product = env['product.template']\n"
       "        products = Product.search([('name', 'ilike', '%' + query + '%')], limit=3)\n"
       "        if products:")

# Replace with debug version
new = ("if len(texto) > 1 and texto[0] == '6':\n"
       "    query = texto[1:].strip()\n"
       "    ret = [{'send_text': 'DEBUG texto=' + repr(texto) + ' query=' + repr(query)}]\n"
       "elif texto == '6':\n"
       "    ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 televisor'}]"
       )

# Actually, we need to be more careful. Let me just add the debug BEFORE the if 
# and leave the rest of the code intact.

# Better approach: add debug right after texto assignment
debug_line = "\n# DEBUG - remove this later\nret = [{'send_text': 'DEBUG texto=' + repr(texto)}]"
# Find a good place to insert
# Actually let's just replace the whole 6-handler section temporarily

# Find where the 6-handler starts
start_marker = 'if len(texto) > 1 and texto[0] == '
end_marker = 'elif texto =='

start_idx = code.find(start_marker)
end_idx = code.find(end_marker, start_idx)

if start_idx >= 0 and end_idx > start_idx:
    # Extract the section
    section = code[start_idx:end_idx]
    print('Found section to replace:')
    print(section[:200])
    print('...')
    
    # Build debug replacement
    debug_section = ("if len(texto) > 1 and texto[0] == '6':\n"
                     "    query = texto[1:].strip()\n"
                     "    ret = [{'send_text': 'DEBUG: texto=' + repr(texto) + ' | query=' + repr(query) + ' | len=' + str(len(query))}]\n")
    
    new_code = code.replace(section, debug_section, 1)
    
    if new_code != code:
        resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot', 'method': 'write',
                'args': [[62], {'code': new_code}], 'kwargs': {}
            }
        })
        if resp2.json().get('result'):
            print('OK - DEBUG code written')
        else:
            print('ERROR:', resp2.json().get('error', {}))
    else:
        print('ERROR: replacement did nothing')
else:
    print('Could not find markers')
    print('start_idx:', start_idx)
    print('end_idx:', end_idx)
    if start_idx < 0:
        # Search for any mention of texto[0]
        idx = code.find('texto[0]')
        if idx >= 0:
            print('Found texto[0] at', idx, 'context:', repr(code[idx:idx+100]))
