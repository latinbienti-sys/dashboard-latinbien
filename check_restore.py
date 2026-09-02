from odoo_conn import get_session

s = get_session()


# Read bot 61
resp61 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[61]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b61 = resp61.json()['result'][0]
print('BOT 61: ' + b61['name'])
print('  Code length: ' + str(len(b61['code'])))
print('  Code empty: ' + str(b61['code'] == ''))
print()

# Read bot 62
resp62 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b62 = resp62.json()['result'][0]
print('BOT 62: ' + b62['name'])
lines = b62['code'].split('\n')
for i in range(min(8, len(lines))):
    print('  L' + str(i+1) + ': ' + repr(lines[i]))
print('  Contains ttype: ' + str('ttype' in b62['code']))
print('  Contains else:: ' + str('else:' in b62['code']))
