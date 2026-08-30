import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Get ALL bots
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[]],
        'kwargs': {'fields': ['id', 'name', 'parent_id', 'connector_id', 'text_match', 'sequence', 'bot_key'],
            'order': 'parent_id,sequence'}
    }
})
bots = resp.json().get('result', [])
bots_by_id = {b['id']: b for b in bots}

def print_tree(bots, parent_id=False, level=0):
    children = [b for b in bots if (b['parent_id'] or [False])[0] == parent_id]
    for b in sorted(children, key=lambda x: (x.get('sequence') or 0, x['id'])):
        conn = str(b['connector_id'][0]) if b['connector_id'] else '-'
        tm = str(b.get('text_match','') or '-')
        bk = str(b.get('bot_key','') or '-')
        prefix = '  ' * level + '└── '
        print(f"{prefix}[C{conn}] Bot {b['id']:>3}: {b['name'][:40]:<40} tm={tm:<20} seq={str(b.get('sequence','0')):<4} key={bk}")
        print_tree(bots, b['id'], level + 1)

print("=== ÁRBOL COMPLETO DE BOTS ===")
print_tree(bots, False)
