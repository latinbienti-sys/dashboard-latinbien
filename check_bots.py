from odoo_conn import get_session

s = get_session()


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
for bot in resp.json()['result']['records']:
    parent = bot.get('parent_id')
    parent_name = parent[1] if parent else 'ROOT'
    bot_id = bot['id']
    name = bot['name']
    # Show relevant bots
    upper = name.upper()
    if ('COMERCIAL' in upper or 'COBRANZA' in upper or 
        'CATCHER' in upper or 'HONDA' in upper or
        'VALIDAR' in upper or
        bot_id in [61, 62, 121, 122, 123, 124, 125]):
        print(f'ID {bot_id:>3}: {name} (parent: {parent_name})')
