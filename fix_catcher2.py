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
code58 = """conv = mess_id.conversation_id
catcher = env['acrux.chat.bot'].browse(61)
if catcher:
    conv.write({'active_bot_id': catcher.id})
ret = env['acrux.chat.bot']"""

if write_bot(58, code58):
    print("✅ Bot 58 (ACCESOS DIRECTO) -> redirige a bot 61")

# =============================================
# FIX 2: Bot 61 - Welcome menu code (Latinbien Commercial)
# =============================================
# Derivated from bot 62 (VALIDAR_CEDULA) menu options for new users
code61 = """conv = mess_id.conversation_id

linea1 = 'Hola! Soy *LatinBot*, tu asistente virtual de Latinbien. \\ud83d\\ude0a\\n'
linea2 = 'Estoy aqui para ayudarte a comprar los productos que deseas de manera facil y rapida.\\n\\n'
linea3 = 'Para comenzar, por favor elige una opcion escribiendo el numero correspondiente:\\n\\n'
linea4 = '1\\ufe0f\\u20e3 Registrarme y solicitar mi Linea de Credito\\n'
linea5 = '2\\ufe0f\\u20e3 Ver el catalogo online y precios\\n'
linea6 = '3\\ufe0f\\u20e3 Compra de contado\\n'
linea7 = '4\\ufe0f\\u20e3 Reportar un problema\\n'
linea8 = '5\\ufe0f\\u20e3 Hablar con un Asesor\\n'
linea9 = '6\\ufe0f\\u20e3 Consultar precio de un producto (escribe 6 + nombre)\\n\\n'
linea10 = '_Si ya tienes una cuenta, puedes escribir tu numero de cedula directamente para identificarte._'
msg = linea1 + linea2 + linea3 + linea4 + linea5 + linea6 + linea7 + linea8 + linea9 + linea10

msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': msg}
back = conv.status
if back == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""

if write_bot(61, code61):
    print("✅ Bot 61 (CATCHER COMERCIAL) -> menú de bienvenida instalado")

# =============================================
# FIX 3: Bot 84 - Remove as root bot
# =============================================
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[84], {'connector_id': False}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print("✅ Bot 84 (TRANSFERENCIA_ASESOR) -> connector cambiado a GLOBAL (no root)")
else:
    print("❌ Bot 84: no se pudo cambiar connector")
