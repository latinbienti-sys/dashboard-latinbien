import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def read_code(bot_id):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bot_id]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    return resp.json()['result'][0]['code']

def write_code(bot_id, code):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bot_id], {'code': code}], 'kwargs': {}
        }
    })
    return resp.json()

# Update all 4 handlers (122-125) to strip "6 " prefix from query
for bot_id in [122, 123, 124, 125]:
    code = read_code(bot_id)
    
    # Add prefix stripping: after getting query, strip "6 " if present
    # Current: query = mess_id.text.strip()
    # New: same but with prefix stripping
    
    old_query = "    query = mess_id.text.strip()"
    new_query = "    query = mess_id.text.strip()\n    if query.startswith('6 '):\n        query = query[2:].strip()"
    
    if old_query in code:
        new_code = code.replace(old_query, new_query, 1)
        # Also update the error message to show the original query for clarity
        # But the error msg uses query, so after stripping it shows just the product name
        
        result = write_code(bot_id, new_code)
        if result.get('result'):
            print('Bot {}: OK - added prefix stripping'.format(bot_id))
        else:
            print('Bot {}: ERROR - {}'.format(bot_id, result.get('error', {})))
    else:
        print('Bot {}: old query line not found'.format(bot_id))
        # Show what we have
        print('  code snippet:', code[:300])
