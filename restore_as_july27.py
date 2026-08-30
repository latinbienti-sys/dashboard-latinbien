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

# Bot 61: COMPLETAMENTE VACÍO (exactamente como bot 34 cobranza)
code61 = "\n  "  # Solo espacios, como bot 34
print(f"Bot 61: vacío {'✅' if write_bot(61, {'code': code61}).get('result') else '❌'}")

# Bot 62: MÍNIMO absoluto - sin funciones, sin navegación
# Solo responder con eco, como bot 45
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
    print(f"Bot 62: eco simple {'✅' if write_bot(62, {'code': code62}).get('result') else '❌'}")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")

print("\n✅ RESTAURADO como el 27/07:")
print("  Bot 61: vacío (igual a bot 34 cobranza)")
print("  Bot 62: solo responde con eco (igual a bot 45)")
print("\nPRUEBA: envía 'hola' al número comercial y dime si recibes 'Recibido: hola'")
