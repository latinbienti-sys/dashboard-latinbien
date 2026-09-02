# -*- coding: utf-8 -*-
import requests, sys
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

# 1) Verificar que los bot_keys destino existen y tienen hijos
print('=== Bot keys destino del goto_and_wait ===')
keys = ['#MENU_RECOMPRA', '#MENU_LC_APROBADA', '#No tienes linea', '#Registro', '#COMERCIAL']
for k in keys:
    r = call('acrux.chat.bot', 'search_read', [[('bot_key', '=', k)]],
             {'fields': ['id', 'name', 'child_ids']})
    if r:
        b = r[0]
        nchilds = len(b.get('child_ids') or [])
        print(f"  {k}: bot={b['id']} ({b['name'][:45]}) hijos={nchilds} {'✅' if nchilds else '❌ SIN HIJOS'}")
    else:
        print(f"  {k}: ❌ NO EXISTE")

# 2) Confirmar que todos los tm=False de comercial estan cubiertos o son seguros
print('\n=== tm=False conector 2 (comercial) - cobertura anti-imagen ===')
bots = call('acrux.chat.bot', 'search_read', [[('connector_id', '=', 2)]],
            {'fields': ['id', 'name', 'text_match', 'code'], 'order': 'id'})
for b in (bots or []):
    if b.get('text_match'):
        continue
    c = b.get('code') or ''
    guardado = "mess_id.ttype != 'text'" in c
    # Bots que NO usan precios (catcher, validar cedula) -> seguros por diseno
    es_precio = any(x in c for x in ['Precio:', 'list_price', 'x_precio_final', 'product_price', 'Resultados para'])
    print(f"  Bot {b['id']} ({b['name'][:40]}): guarda={guardado} precio={es_precio}")
    if es_precio and not guardado:
        print("      ❌❌❌ BOT DE PRECIOS SIN GUARDA")

# 3) Buscar en TODOS los bots de comercial cualquier rastro de busqueda de precios sin guarda
print("\n=== Bots con 'Precio'/'Resultados' en comercial ===")
for b in (bots or []):
    c = b.get('code') or ''
    if 'Resultados para' in c or 'Precio:' in c or 'x_precio_final' in c:
        guardado = "mess_id.ttype != 'text'" in c
        print(f"  Bot {b['id']} ({b['name'][:40]}): guarda={'✅' if guardado else '❌'}")
