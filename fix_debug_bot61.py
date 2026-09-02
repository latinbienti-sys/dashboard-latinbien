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

# Bot 61: código con MANEJO DE ERRORES y LOG
code61 = """try:
  import inspect
  _logger = inspect.currentframe().f_globals.get('_logger')
  
  conv = mess_id.conversation_id
  texto = (mess_id.text or '').strip()
  
  if _logger:
    _logger.warning(f'BOT61_MESSAGE: conv={conv.id} texto={texto!r} status={conv.status}')
  
  msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'BOT61: Recibido: ' + texto}
  back_status = conv.status
  if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
  else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
    
  if _logger:
    _logger.warning(f'BOT61_SUCCESS: message sent to conv {conv.id}')
except Exception as e:
  try:
    env['ir.logging'].create({'name': 'BOT61_CRASH', 'type': 'server', 'level': 'ERROR', 'message': str(e)[:500], 'dbname': 'erp_production'})
  except:
    pass"""

resp = write_bot(61, {'code': code61})
print(f"Bot 61: {'✅' if resp.get('result') else '❌'}")
if not resp.get('result'):
    print(json.dumps(resp, indent=2)[:500])

# Bot 62: similar con try/except
code62 = """try:
  import inspect
  _logger = inspect.currentframe().f_globals.get('_logger')
  
  conv = mess_id.conversation_id
  texto = (mess_id.text or '').strip()
  
  if _logger:
    _logger.warning(f'BOT62_MESSAGE: conv={conv.id} texto={texto!r} status={conv.status}')
  
  msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'BOT62: Recibido: ' + texto}
  back_status = conv.status
  if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
  else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')
    
  if _logger:
    _logger.warning(f'BOT62_SUCCESS: message sent to conv {conv.id}')
except Exception as e:
  try:
    env['ir.logging'].create({'name': 'BOT62_CRASH', 'type': 'server', 'level': 'ERROR', 'message': str(e)[:500], 'dbname': 'erp_production'})
  except:
    pass"""

resp = write_bot(62, {'code': code62})
print(f"Bot 62: {'✅' if resp.get('result') else '❌'}")
