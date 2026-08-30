import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Updated code: use message's connector instead of connector 13
code44 = """try:
  wizard = env['acrux.chat.message.wizard']
  connector_id = mess_id.connector_id
  
  Conv = env['acrux.chat.conversation']

  number = '584247391806'
  conv_id = Conv.search([('connector_id', '=', connector_id.id), ('number', '=', number)], limit=1)
  if not conv_id:
    partner_id = env['res.partner'].search([('mobile','=',number)])
    conv_id = Conv.conversation_create(partner_id, connector_id.id, number)
  
  text = \"\"\"\\U0001f44b\\U0001f3fc !Saludos Cobranzas!, soy \\U0001f916 *LatinBot*: Tu *Asistente Virtual*, te aviso que el cliente  *\"\"\"+ mess_id.contact_id.name +\"\"\"* con el n\\u00famero \"\"\"+ mess_id.contact_id.number +\"\"\" esta esperando en el ChatRoom para ser atendido\"\"\"
  
  txt_mes = {'ttype': 'text',
                     'from_me': True,
                     'contact_id': conv_id.id,
                     'text': text}
  msg_datas = [txt_mes]
  back_status = conv_id.status
  if back_status == 'current':
    conv_id.send_message_bus_release(msg_datas[0], 'current',False)
  else:
    conv_id.block_conversation()
    conv_id.send_message_bus_release(msg_datas[0], 'done')
    
  \"\"\"mess_id.contact_id.write({
    'agent_id': 12,
    'status': 'current'
  })\"\"\"

except Exception as error:
  raise UserError('Error: \\"' + str(error))"""

code47 = code44.replace("!Saludos Cobranzas!", "!Saludos Ejecutivo de Cobranza!")

# Verify syntax
try:
    compile(code44, '<string>', 'exec')
    compile(code47, '<string>', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error: {e}')
    exit()

# Update bot 44
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[44], {'code': code44}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print('\\u2705 Bot 44 (ASESOR) actualizado')
else:
    print('\\u274c Bot 44 Error:', resp.json().get('error', {}))

# Update bot 47
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[47], {'code': code47}], 'kwargs': {}
    }
})
if resp2.json().get('result'):
    print('\\u2705 Bot 47 (ASESOR fuera de horario) actualizado')
else:
    print('\\u274c Bot 47 Error:', resp2.json().get('error', {}))
