from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Check ALL bots for ret = [...] pattern
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'name', 'code', 'parent_id', 'active'],
            'domain': [['active', 'in', [True, False]]],
            'limit': 200
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    
    print('Bots que usan ret = [...] (necesitan corrección):')
    found = []
    for bot in records:
        code = bot.get('code') or ''
        if 'ret =' in code and bot['id'] != 62:  # Bot 62 already fixed
            parent = bot.get('parent_id')
            if isinstance(parent, (list, tuple)):
                parent = parent[0] if parent else 0
            active = bot.get('active', True)
            lines = len(code.split('\n'))
            found.append((bot['id'], bot['name'], parent, active, lines))
    
    # Sort by parent for tree view
    found.sort(key=lambda x: (x[2], x[0]))
    for bid, name, parent, active, lines in found:
        status = '🟢' if active else '🔴'
        print(f'  {status} Bot {bid}: {name} | parent={parent} | {lines} líneas')
    
    if not found:
        print('  ✅ No hay otros bots con ret = [...]')
    print()

    # Also check ALL bot codes for the ret pattern to be thorough
    print('Verificación rápida de todo el árbol:')
    for bot in records:
        code = bot.get('code') or ''
        if not code.strip():
            continue
        if bot['id'] == 62:  # Already fixed
            continue
        has_ret = 'ret =' in code
        # Count ret occurrences
        ret_count = code.count('ret =')
        if ret_count > 0:
            lines = len(code.split('\n'))
            print(f'  Bot {bot["id"]}: {bot["name"]} | {ret_count}x ret= | {lines} líneas')
