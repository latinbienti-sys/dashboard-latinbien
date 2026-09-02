from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# 1. Check WhatsApp channels/numbers and which bot they use
print('=== WhatsApp Channels/Accounts ===')
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.account/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.account', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['id', 'name', 'bot_id', 'platform', 'active'], 'domain': []}
    }
})
r = resp.json()['result']
accounts = r.get('records', r) if isinstance(r, dict) else r
for acc in accounts:
    bot = acc.get('bot_id')
    bot_name = bot[1] if bot else 'NONE'
    print(f'  Acct {acc["id"]}: {acc["name"]} (platf: {acc.get("platform")}) -> Bot: {bot_name}')

print()

# 2. Search for #MENUPRINCIPAL label
print('=== Searching for MENUPRINCIPAL label ===')
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'code', 'text_match', 'label'],
            'domain': [['label', '=', 'MENUPRINCIPAL']],
        }
    }
})
r2 = resp2.json()['result']
labels = r2.get('records', r2) if isinstance(r2, dict) else r2
if labels:
    for lb in labels:
        print(f'  ID {lb["id"]}: {lb["name"]} (text_match: {lb.get("text_match")}) label={lb.get("label")}')
else:
    print('  No bot found with label MENUPRINCIPAL')
print()

# 3. Check if there's a bot 34 code change
resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[34]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b34 = resp3.json()['result'][0]
print(f'Bot 34 code length: {len(b34["code"])}')
print(f'Bot 34 code repr: {repr(b34["code"])}')
