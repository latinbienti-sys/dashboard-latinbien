import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Make bot 62 EXACTLY like bot 45 - NO ret = env, just implicit None
code62 = """conv = mess_id.conversation_id
texto = (mess_id.text or '').strip()
msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Recibido: ' + texto}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')"""

try:
    compile(code62, '<string>', 'exec')
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': code62}], 'kwargs': {}
        }
    })
    if resp.json().get('result'):
        print("✅ Bot 62: exactamente como bot 45 (sin ret = env)")
    else:
        print("❌ Error")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
