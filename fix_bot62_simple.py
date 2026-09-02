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

# Simpler version - just echo with try/except
code62 = """try:
  conv = mess_id.conversation_id
  texto = (mess_id.text or '').strip()
  msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Recibido: ' + texto}
  back_status = conv.status
  if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
  else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
except Exception as e:
  env['ir.logging'].create({'name': 'BOT62_ERROR', 'type': 'server', 'level': 'ERROR', 'message': str(e), 'dbname': 'erp_production'})"""

resp = write_bot(62, {'code': code62})
print("Write result:", json.dumps(resp, indent=2)[:500])
