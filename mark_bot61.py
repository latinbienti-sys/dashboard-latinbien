import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Put marker code in bot 61 - just says it ran
code61 = """conv = mess_id.conversation_id
m = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'BOT61_RUN'}
try:
    conv.send_message_bus_release(m, 'current', False)
except:
    try:
        conv.send_message_bus_release(m, 'done')
    except:
        pass
ret = env['acrux.chat.bot']"""

try:
    compile(code61, '<string>', 'exec')
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[61], {'code': code61}], 'kwargs': {}
        }
    })
    if resp.json().get('result'):
        print("✅ Bot 61: marcador instalado")
    else:
        print("❌ Error")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
