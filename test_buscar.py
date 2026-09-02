import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Test: buscar productos con el mismo codigo que BUSCAR_PRODUCTO usaria
# Simular lo que hace el bot
query = 'televisor 32'
Product = session.post('https://latinbien.com/web/dataset/call_kw/product.template/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'product.template', 'method': 'search_read',
        'args': [[['name', 'ilike', '%' + query + '%']]],
        'kwargs': {'fields': ['id', 'name', 'list_price'], 'limit': 3}
    }
})
prods = Product.json().get('result', [])
print(f'Resultados para "televisor 32": {len(prods)}')
for p in prods:
    precio = p.get('list_price', 0)
    if precio:
        inicial = round(precio * 0.30, 2)
        cuota = round((precio - inicial) / 20, 2)
        print(f'  {p["name"]} - ${precio}')
        print(f'    Inicial 30%: ${inicial}, 20 cuotas de: ${cuota}')
    else:
        print(f'  {p["name"]} - Precio: $0 (consultar)')

# Ahora verificar el bot 101 (BUSCAR_PRODUCTO) y su codigo completo
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['id', '=', 101]]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'bot_key']}
    }
})
bot = resp.json().get('result', [])
if bot:
    b = bot[0]
    print(f'\nBot 101 {b["name"]}:')
    print(f'  text_match={b.get("text_match")} (debe ser False para handler)')
    print(f'  bot_key={b.get("bot_key")}')
    print(f'  code:\n{b.get("code", "")}')
