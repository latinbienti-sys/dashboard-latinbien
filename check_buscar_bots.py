from odoo_conn import get_session

s = get_session()


# Check all BUSCAR_EN bots + CONSULTA_PRECIO bots
bots = [122, 123, 124, 125, 118, 119, 120, 121]
for bid in bots:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    r = resp.json()['result'][0]
    c = r['code'] or ''
    if 'list_price' in c or 'Precio:' in c or 'x_precio_final' in c:
        print(f'=== {r["name"]} (ID={r["id"]}) ===')
        for i, line in enumerate(c.split('\n'), 1):
            l = line.strip()
            if any(x in l for x in ['Precio:', 'Inicial', 'cuota', 'list_price', 'x_precio_final', 'format(precio)']):
                print(f'  {i}: {l}')
        print()
