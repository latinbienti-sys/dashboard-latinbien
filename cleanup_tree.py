import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

print('=== LIMPIEZA DE ÁRBOL ===')
print()

# 1. Assign cobranza bots to connector 17
cobranza_bots = {
    45: 'NOT FOUND',
    47: 'ASESOR (CONECTOR DE COBRANZA) fuera de horario'
}

print('Asignando connector=17 a bots de cobranza:')
for bid, name in cobranza_bots.items():
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], {'connector_id': 17}], 'kwargs': {}
        }
    })
    r = resp.json()
    if r.get('result'):
        print(f'  ✅ Bot {bid}: {name} → connector=17')
    else:
        print(f'  ❌ Bot {bid}: {name} → Error: {r.get("error",{}).get("message","")[:100]}')

print()

# 2. Assign global bots to connector 2 (comercial)
global_bots = {
    59: 'MOTORIZADO (DIRECTO)',
    84: 'TRANSFERENCIA_ASESOR'
}

print('Asignando connector=2 a bots globales:')
for bid, name in global_bots.items():
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], {'connector_id': 2}], 'kwargs': {}
        }
    })
    r = resp.json()
    if r.get('result'):
        print(f'  ✅ Bot {bid}: {name} → connector=2')
    else:
        print(f'  ❌ Bot {bid}: {name} → Error: {r.get("error",{}).get("message","")[:100]}')

print()
print('=== VERIFICACIÓN FINAL ===')
print()

# Verify all changes
for bid in [45, 47, 59, 84]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'connector_id', 'active']}
        }
    })
    r = resp.json()
    if 'result' in r and r['result']:
        bot = r['result'][0]
        conn = bot.get('connector_id')
        if isinstance(conn, (list, tuple)):
            conn = f'{conn[0]}' if conn else 'None'
        print(f'  Bot {bid}: {bot["name"]} | connector={conn} | active={bot.get("active",True)}')
