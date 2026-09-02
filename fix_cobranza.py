# -*- coding: utf-8 -*-
# FIX COBRANZA (conector 17): bots 40, 41, 45
# - conversation_id -> contact_id
# - eliminar active_bot_id (no existe); el EXIT natural devuelve al catcher
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

def get_code(bid):
    bots = call('acrux.chat.bot', 'search_read', [[('id', '=', bid)]], {'fields': ['id', 'code']})
    return bots and bots[0].get('code') or ''

def safe_write(bid, name, code):
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        print(f'❌ SYNTAX {name}: {e}')
        return
    res = call('acrux.chat.bot', 'write', [[bid], {'code': code}])
    print(f'✅ Bot {bid} ({name}): {res}')

# ============ BOT 40: PAGAR Y REPORTAR ============
code40 = """conv = mess_id.contact_id
partner = search_partner()
if partner:
    p = partner[0]
    texto = f\"\"\"🤖 *LatinBot:* Estimado/a *{p.name or ''}*,

*¡Paga y reporta tu cuota!* a través de nuestro portal WEB,
Inicia sesión con: *{p.email or ''}* siguiendo el enlace 🔗 👉 {p.signup_url or 'https://latinbien.com/web/login'}

¿Cómo reportar tu pago a través del portal?

1. Ingresa con tu usuario en la Web de latinbien
2. Busca la opción *\"PagosLatinbien\"*
3. Ingresa los datos solicitados y ¡Listo! ya puedes reportar tu pago

¡Lo hacemos fácil y rápido para ti!🚀
    \"\"\"
    msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': texto}
    back = conv.status
    if back == 'current':
        conv.send_message_bus_release(msg_data, 'current', False)
    else:
        conv.block_conversation()
        conv.send_message_bus_release(msg_data, 'done')
else:
    msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': '🤖 *LatinBot:* No logramos identificarte automáticamente. Por favor escribe *5* para hablar con un asesor y te ayudaremos a pagar o reportar tu cuota.'}
    back = conv.status
    if back == 'current':
        conv.send_message_bus_release(msg_data, 'current', False)
    else:
        conv.block_conversation()
        conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""
safe_write(40, 'PAGAR Y REPORTAR', code40)

# ============ BOT 41: ESTADO DE CUENTA (largo) ============
code41 = get_code(41)
orig41 = code41
# 1. conversation_id -> contact_id
code41 = code41.replace('mess_id.conversation_id', 'mess_id.contact_id')
# 2. eliminar bloque active_bot_id (con variantes de espaciado)
import re
code41 = re.sub(r"target = env\['acrux\.chat\.bot'\]\.search\(\[\('name', 'ilike', '%CATCHER%'\)\], limit=1\)\s*\n?\s*if target:\s*\n?\s*conv\.write\(\{'active_bot_id': target\.id\}\)", '', code41)
code41 = re.sub(r"\ntarget = env\['acrux\.chat\.bot'\]\.search\(\[\('name', 'ilike', '%CATCHER%'\)\], limit=1\)\n\nif target:\n\n    conv\.write\(\{'active_bot_id': target\.id\}\)", '\n', code41)
# 3. quitar cualquier line residual con active_bot_id
code41 = re.sub(r"[^\n]*active_bot_id[^\n]*\n?", '', code41)
# 4. quitar lineas residuales de target search
code41 = re.sub(r"[^\n]*%CATCHER%[^\n]*\n?", '', code41)
if code41 != orig41:
    safe_write(41, 'ESTADO DE CUENTA', code41)
else:
    print('⚠️ Bot 41: no hubo cambios detectados')
    print(code41[:300])

# ============ BOT 45: NOT FOUND ============
code45 = get_code(45)
orig45 = code45
code45 = code45.replace('mess_id.conversation_id', 'mess_id.contact_id')
if code45 != orig45:
    safe_write(45, 'NOT FOUND', code45)
else:
    print('⚠️ Bot 45: no hubo cambios')

# ============ VERIFICAR ============
print('\n=== VERIFICACION GLOBAL ===')
bots = call('acrux.chat.bot', 'search_read', [[]], {'fields': ['id', 'name', 'code']})
pend = [b for b in (bots or []) if b.get('code') and ('conversation_id' in b['code'] or 'active_bot_id' in b['code'])]
if pend:
    for b in pend:
        print(f"   ⚠️ Bot {b['id']} ({b['name'][:45]}) aun tiene conversation_id/active_bot_id")
else:
    print('   ✅ Ningun bot del sistema usa campos inexistentes')
