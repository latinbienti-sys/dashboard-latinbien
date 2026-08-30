# -*- coding: utf-8 -*-
# Identificar todos los bots del conector 2 (y 17) con text_match=False que procesan
# busquedas/precios y que por tanto capturan imagenes/PDFs como si fueran consultas
import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
API = 'https://latinbien.com/web/dataset/call_kw'
def call(model, method, args, kwargs=None):
    resp = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return resp.json().get('result')

bots = call('acrux.chat.bot', 'search_read', [[('connector_id', 'in', [2, 17])]],
            {'fields': ['id', 'name', 'bot_key', 'text_match', 'parent_id', 'connector_id', 'code'],
             'order': 'id'})
print(f'Total bots conn 2 y 17: {len(bots or [])}')
print('\n=== Bots tm=False (capturan CUALQUIER mensaje) ===')
for b in (bots or []):
    conn = b.get('connector_id')
    if b.get('text_match'):
        continue
    code = b.get('code') or ''
    # marcar si parece de busqueda/precio
    es_precio = any(k in code for k in ['Precio:', 'list_price', 'x_precio_final', 'price', 'precio', 'buscar', 'search', 'product'])
    par = b.get('parent_id')
    print(f"  Bot {b['id']} [{conn[1] if conn else '?'}] key={b.get('bot_key')} tm={b.get('text_match')!r} parent={par[0] if par else 'ROOT'} {'*** PRECIO/BUSQUEDA ***' if es_precio else ''}")
    print(f"      name={b['name']}")
    if es_precio:
        print(f"      code_head={code[:160]!r}")
