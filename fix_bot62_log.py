import requests, json, sys, datetime
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

# Rewrite bot 62 with logging: always writes to ir.logging AND sends message
code62 = """import logging
_logger = logging.getLogger('acrux.chat.bot.62')

conv = mess_id.conversation_id
texto = (mess_id.text or '').strip()
_logger.warning(f'BOT62 EJECUTANDO: texto={texto!r} conv={conv.id} status={conv.status}')

msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Recibido: ' + texto}
back_status = conv.status
if back_status == 'current':
    conv.send_message_bus_release(msg_data, 'current', False)
else:
    conv.block_conversation()
    conv.send_message_bus_release(msg_data, 'done')"""

try:
    compile(code62, '<string>', 'exec')
    if write_bot(62, {'code': code62}):
        print("✅ Bot 62 actualizado con logging")
    else:
        print("❌ Error")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")

# Now check ALL conversations for number 584147305385 (Yarley's test)
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[('number','=','584147305385')],
        'fields':['id','status','active_bot_id','write_date'],
        'limit':5
    }
})
records = resp.json().get('result', {}).get('records', [])
print(f"\nConversaciones para 584147305385:")
for r in records:
    active = r.get('active_bot_id')
    active_name = f'bot_{active[0]}' if isinstance(active, list) else 'NONE'
    print(f"  ID {r['id']}: status={r['status']} active={active_name}")
