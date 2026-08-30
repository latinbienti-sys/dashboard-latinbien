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
    return resp.json()

# Bot 61: MÍNIMO absoluto - solo enviar texto, como bot 45
code61 = """conv = mess_id.conversation_id
text = 'Hola desde bot 61 - prueba minimal'
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': text}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')"""

resp = write_bot(61, {'code': code61})
print(f"Bot 61: {'✅' if resp.get('result') else '❌'}")

# Bot 62: MÍNIMO - solo texto, como bot 45
code62 = """conv = mess_id.conversation_id
texto = (mess_id.text or '').strip()
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Bot62 recibio: ' + texto}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')"""

resp = write_bot(62, {'code': code62})
print(f"Bot 62: {'✅' if resp.get('result') else '❌'}")
