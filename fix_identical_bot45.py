import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Bot 61: código MÍNIMO IDÉNTICO a bot 45
code61 = """conv = mess_id.conversation_id
text = 'BOT61 MENSAJE DE PRUEBA - ignora esto'
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': text}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')"""

resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'write',
        'args':[[61],{'code':code61}],'kwargs':{}
    }
})
print(f"Bot 61 IDÉNTICO a bot 45: {'✅' if resp.json().get('result') else '❌'}")

# Also RESTORE bot 62 to same minimal pattern
code62 = """conv = mess_id.conversation_id
texto = (mess_id.text or '').strip()
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'BOT62: ' + texto}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')"""

resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'write',
        'args':[[62],{'code':code62}],'kwargs':{}
    }
})
print(f"Bot 62 IDÉNTICO a bot 45: {'✅' if resp.json().get('result') else '❌'}")
