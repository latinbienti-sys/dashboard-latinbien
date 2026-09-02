import requests, json

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get all bots with their parent hierarchy
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'parent_id', 'text_match'],
            'order': 'id asc',
            'domain': []
        }
    }
})
r = resp.json()['result']
bots = r.get('records', r) if isinstance(r, dict) else r

# Build parent map
bot_map = {b['id']: b for b in bots}

def get_parent_chain(bot_id):
    chain = []
    current = bot_id
    while current:
        bot = bot_map.get(current)
        if bot:
            chain.append(bot['name'])
            current = bot['parent_id'] and bot['parent_id'][0]
        else:
            break
    return ' > '.join(reversed(chain))

print('=== ALL BOTS ===')
for b in bots:
    chain = get_parent_chain(b['id'])
    tm = ' [TEXT_MATCH]' if b.get('text_match') else ''
    print(f'ID {b["id"]:>3}: {b["name"]}{tm}')
    print(f'        Path: {chain}')
    print()
