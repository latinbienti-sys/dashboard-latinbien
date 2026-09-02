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

# Bot 61: Send welcome menu AND navigate to bot 62
code61 = """conv = mess_id.conversation_id
text = '''🚗 *¡Bienvenido a Honda Mérida!* ✨
Tu próximo Honda está aquí. Soy tu asesor virtual y estoy listo para ayudarte a estrenar.

Por favor, selecciona una de las siguientes opciones escribiendo el *NÚMERO*:

1️⃣ *Modelos Nuevos 2026* (Civic, CR-V, HR-V, City, BR-V)
2️⃣ *Solicitar Cotización y Planes de Financiamiento* 📊
3️⃣ *Agendar una Prueba de Manejo* 🏁
4️⃣ *Autos Seminuevos Garantizados* 🚗
5️⃣ *Agendar Cita de Servicio / Taller* 🔧
6️⃣ *Hablar con un Asesor Humano* 🧑‍💼

_Escribe solo el número de la opción que deseas y te daré la información de inmediato._'''

msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': text}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')

# Navigate to bot 62 (VALIDAR CEDULA)
ret = env['acrux.chat.bot'].browse(62)"""

try:
    compile(code61, '<string>', 'exec')
    if write_bot(61, {'code': code61}):
        print("✅ Bot 61: menú + navegación a bot 62")
    else:
        print("❌ Error en bot 61")
except SyntaxError as e:
    print(f"❌ Syntax error bot 61: {e}")

# Bot 62: Echo + navigate back to itself (to keep processing)
code62 = """conv = mess_id.conversation_id
texto = (mess_id.text or '').strip()
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Recibido: ' + texto}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')

# Stay on this bot for next message
ret = env['acrux.chat.bot'].browse(62)"""

try:
    compile(code62, '<string>', 'exec')
    if write_bot(62, {'code': code62}):
        print("✅ Bot 62: echo + permanece en bot 62")
    else:
        print("❌ Error en bot 62")
except SyntaxError as e:
    print(f"❌ Syntax error bot 62: {e}")
