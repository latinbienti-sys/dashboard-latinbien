import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

def write_bot(bid, code):
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        print(f'❌ Bot {bid}: SYNTAX ERROR L{e.lineno}: {e.msg}')
        return False
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], {'code': code}], 'kwargs': {}
        }
    })
    return resp.json().get('result', False)

# =============================================
# FIX 1: Bot 58 - redirect ALL users to bot 61
# =============================================
code58 = """# Redirigir al CATCHER (bot 61) para que muestre el menú
conv = mess_id.conversation_id
catcher = env['acrux.chat.bot'].browse(61)
if catcher:
    conv.write({'active_bot_id': catcher.id})
else:
    # Fallback: si no existe bot 61, mostrar menú mínimo
    msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Bienvenido a Honda Mérida. Escribe 1 para ver modelos nuevos.'}
    conv.send_message_bus_release(msg_data, 'current', False)
ret = env['acrux.chat.bot']"""

if write_bot(58, code58):
    print("✅ Bot 58 (ACCESOS DIRECTO) -> redirige a bot 61")

# =============================================
# FIX 2: Bot 61 - Welcome menu code
# =============================================
code61 = """conv = mess_id.conversation_id
msg = '''🚗 *\\u00a1Bienvenido a Honda M\\u00e9rida!* \\u2728
Tu pr\\u00f3ximo Honda est\\u00e1 aqu\\u00ed. Soy tu asesor virtual y estoy listo para ayudarte a estrenar.

Por favor, selecciona una de las siguientes opciones escribiendo el *N\\u00daMERO*:

1\\ufe0f\\u20e3 *Modelos Nuevos 2026* (Civic, CR-V, HR-V, City, BR-V)
2\\ufe0f\\u20e3 *Solicitar Cotizaci\\u00f3n y Planes de Financiamiento* \\ud83d\\udcca
3\\ufe0f\\u20e3 *Agendar una Prueba de Manejo* \\ud83c\\udfc1
4\\ufe0f\\u20e3 *Autos Seminuevos Garantizados* \\ud83d\\ude97
5\\ufe0f\\u20e3 *Agendar Cita de Servicio / Taller* \\ud83d\\udd27
6\\ufe0f\\u20e3 *Hablar con un Asesor Humano* \\ud83e\\uddd1\\u200d\\ud83d\\udcbc

_Escribe solo el n\\u00famero de la opci\\u00f3n que deseas y te dar\\u00e9 la informaci\\u00f3n de inmediato._'''

msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': msg}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""

if write_bot(61, code61):
    print("✅ Bot 61 (CATCHER COMERCIAL) -> código de bienvenida instalado")

# =============================================
# FIX 3: Bot 84 - Remove as root bot
# =============================================
# Check current connector of bot 84
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[84]],
        'kwargs': {'fields': ['id', 'name', 'connector_id', 'parent_id']}
    }
})
b84 = resp.json()['result'][0]
print(f"Bot 84 actual: connector={b84['connector_id']}, parent={b84['parent_id']}")

# Set connector_id to False (global / not root for any connector)
# and keep parent as root
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[84], {'connector_id': False}], 'kwargs': {}
    }
})
if resp2.json().get('result'):
    print("✅ Bot 84 (TRANSFERENCIA_ASESOR) -> connector cambiado a GLOBAL (no root)")
else:
    print("❌ Bot 84: no se pudo cambiar connector")
