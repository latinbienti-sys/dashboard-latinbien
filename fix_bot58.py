import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

print('=== FIX BOT 58 (ACCESOS DIRECTO) ===')

# Fix connector first
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[58], {'connector_id': 2}], 'kwargs': {}
    }
})
print(f'  Connector=2: {"✅" if resp.json().get("result") else "❌"}')

# New code without ret = [...]
new_code_58 = """# Acceso directo para clientes
partner = search_partner()
conv = mess_id.conversation_id

if partner:
    text = f\"\"\"\\U0001f916 *LatinBot:* Estimado/a cliente *{str(partner[0].name)}*,

Ahora *puedes reportar tu pago a trav\\u00e9s de nuestro portal WEB latinbien.com*

Inicia sesi\\u00f3n con: *{partner[0].email}* 

Siguiendo el enlace \\U0001f517 \\U0001f449 {partner[0].signup_url}


Atte.
*Equipo de Cuentas por Cobrar*
*LATINBIEN*
    \"\"\"
    
    msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': text}
    
    # Navegar a CATCHER (bot 61)
    catcher = env['acrux.chat.bot'].browse(61)
    if catcher:
        conv.write({'active_bot_id': catcher.id})
    
    back_status = conv.status
    if back_status == 'current':
        conv.send_message_bus_release(msg_data, 'current', False)
    else:
        conv.block_conversation()
        conv.send_message_bus_release(msg_data, 'done')"""

try:
    compile(new_code_58, '<string>', 'exec')
    print('  Sintaxis OK')
    
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[58], {'code': new_code_58}], 'kwargs': {}
        }
    })
    print(f'  C\\u00f3digo actualizado: {"✅" if resp2.json().get("result") else "❌"}')
except SyntaxError as e:
    print(f'  Syntax error: {e}')

print()
print('=== PASO 3: Corregir Bot 62 (VALIDAR_CEDULA) ===')

# Read full code of bot 62
resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match', 'connector_id', 'active']}
    }
})
r3 = resp3.json()
if 'result' in r3 and r3['result']:
    bot62 = r3['result'][0]
    code62 = bot62.get('code', '')
    print(f'  Bot 62: {bot62["name"]}')
    print(f'  Active: {bot62.get("active",True)} | Connector: {bot62.get("connector_id")} | TextMatch: {bot62.get("text_match","")}')
    print(f'  Code length: {len(code62)} chars, {len(code62.split(chr(10)))} lines')
    print()
    print('  Full code:')
    print(code62)
