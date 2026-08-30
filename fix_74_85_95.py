import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

def write_bot(bid, code):
    # Verify compiles
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        print(f'❌ Bot {bid}: SYNTAX ERROR L{e.lineno}: {e.msg}')
        return False
    
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], {'code': code}], 'kwargs': {}
        }
    })
    return resp.json().get('result', False)

# === BOT 85: RECOMPRA_CONVENIO ===
code85 = """try:
    partner = search_partner()
    if partner:
        p = partner[0]
        es_convenio = False
        try:
            es_convenio = (p.x_tipo_de_solicitante == 'B')
        except:
            pass
        if es_convenio:
            nom_conv = ''
            try:
                if p.x_convenio_afiliado:
                    nom_conv = p.x_convenio_afiliado.name
            except:
                pass
            msg = '\\u00a1Qu\\u00e9 gran beneficio, *' + (p.name or '') + '*! Puedes disfrutar de nuestro convenio activo con *' + nom_conv + '*.'
            conv = mess_id.conversation_id
            msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': msg}
            back = conv.status
            if back == 'current':
                conv.send_message_bus_release(msg_data, 'current', False)
            else:
                conv.block_conversation()
                conv.send_message_bus_release(msg_data, 'done')
        else:
            msg = 'Hola ' + (p.name or '') + ', en mi sistema no registras un convenio activo.'
            conv = mess_id.conversation_id
            msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': msg}
            back = conv.status
            if back == 'current':
                conv.send_message_bus_release(msg_data, 'current', False)
            else:
                conv.block_conversation()
                conv.send_message_bus_release(msg_data, 'done')
    else:
        conv = mess_id.conversation_id
        msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Para verificar tus beneficios de Convenio Corporativo, escribe la palabra "ASESOR".'}
        back = conv.status
        if back == 'current':
            conv.send_message_bus_release(msg_data, 'current', False)
        else:
            conv.block_conversation()
            conv.send_message_bus_release(msg_data, 'done')
except Exception as e:
    conv = mess_id.conversation_id
    msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Error al validar convenio: '}
    back = conv.status
    if back == 'current':
        conv.send_message_bus_release(msg_data, 'current', False)
    else:
        conv.block_conversation()
        conv.send_message_bus_release(msg_data, 'done')
ret = env['acrux.chat.bot']"""

# === BOT 74: LC_CONVENIO (same code as 85) ===
code74 = code85

# === BOT 95: REG_CONVENIO (same code as 85) ===
code95 = code85

for bid, c in [(85, code85), (74, code74), (95, code95)]:
    ok = write_bot(bid, c)
    print(f'✅ Bot {bid} fixed' if ok else f'❌ Bot {bid} failed')
