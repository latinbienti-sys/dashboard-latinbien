import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Restore bot 34 to original code (newline + 2 spaces)
orig_bot34 = "\n  "
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[34], {'code': orig_bot34}], 'kwargs': {}
    }
})
print('Bot 34 restore:', 'OK' if resp.json().get('result') else 'ERROR')

# Restore bot 45 to original code
orig_bot45 = "# I'm waiting on the menu\nret=[{'goto_and_wait': '#MENUPRINCIPAL'}, {'send_text': '\\U0001f916 *LatinBot*: Disculpa, no puedo entenderte, por favor *\"Escribe en el Chat \\U0001f4e3 SOLO EL NUMERO\"* de la opci\\u00f3n que quieras elegir:  \\U0001f449 *1, 2, 3, 4, 5, #* \\U0001f448'}]"
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[45], {'code': orig_bot45}], 'kwargs': {}
    }
})
print('Bot 45 restore:', 'OK' if resp2.json().get('result') else 'ERROR')

# Verify
for bid in [34, 45]:
    resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    b = resp3.json()['result'][0]
    print(f'  Bot {b["id"]}: {repr(b["code"][:80])}')
