import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

def write_bot(bid, data):
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], data], 'kwargs': {}
        }
    })
    return resp.json().get('result', False)

# Bot 61: Preguntar cédula y navegar a bot 62
code61 = """conv = mess_id.conversation_id
text = '''🚗 *¡Bienvenido a Honda Mérida!* ✨
Por favor, ingresa tu *cédula de identidad* para validar tus datos y mostrarte las mejores opciones.

*Ejemplo:* V12345678'''
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': text}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
# Navegar a bot 62 para validar la cédula
ret = env['acrux.chat.bot'].browse(62)"""

if write_bot(61, {'code': code61}):
    print("✅ Bot 61: pide cédula + navega a bot 62")
else:
    print("❌ Error bot 61")

# Bot 62: Echo + se mantiene activo
code62 = """conv = mess_id.conversation_id
texto = (mess_id.text or '').strip()
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Recibido: ' + texto}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot'].browse(62)"""

if write_bot(62, {'code': code62}):
    print("✅ Bot 62: echo + permanece activo")
else:
    print("❌ Error bot 62")
