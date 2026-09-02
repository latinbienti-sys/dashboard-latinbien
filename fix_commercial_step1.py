import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

print('=== PASO 1: Asignar connector=2 a bots comerciales sin connector ===')
print()

# Bots del árbol comercial que tienen connector=None
commercial_global_bots = [
    97, 122, 102, 106, 118,  # RECOMPRA
    98, 103, 107, 119, 123,  # LC
    99, 104, 108, 120, 124,  # REG
    100, 105, 109, 121, 125, # NR
    101, 117,  # BUSCAR
]

# Also inactive bots that should be commercial
other_global = [2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 56, 57, 60, 35, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 28, 29, 30, 31, 32, 33]

# Set ALL to connector=2
all_bots = commercial_global_bots

success = 0
error = 0
for bid in all_bots:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], {'connector_id': 2}], 'kwargs': {}
        }
    })
    if resp.json().get('result'):
        success += 1
    else:
        error += 1
        print(f'  ❌ Bot {bid}: {resp.json().get("error",{}).get("message","")[:80]}')

print(f'✅ {success} bots asignados a connector=2')
if error:
    print(f'❌ {error} errores')

print()
print('=== PASO 2: Verificar Bot 58 (ACCESOS) ===')
# Read bot 58 full code
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[58]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'connector_id', 'active']}
    }
})
r = resp.json()
if 'result' in r and r['result']:
    bot58 = r['result'][0]
    print(f'  Bot 58: {bot58["name"]}')
    print(f'  Active: {bot58.get("active",True)} | Connector: {bot58.get("connector_id")} | TextMatch: {bot58.get("text_match","")}')
    code58 = bot58.get('code', '')
    print(f'  Current code ({len(code58)} chars)')
    print(f'  Has ret: {"ret =" in code58}')
