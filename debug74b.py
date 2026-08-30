code = '''try:
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
            ret = [{'send_text': msg}]
        else:
            msg = 'Hola ' + (p.name or '') + ', en mi sistema no registras un convenio activo.'
            ret = [{'send_text': msg}]
    else:
        conv = mess_id.conversation_id
        msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'test'}
        back = conv.status
        if back == 'current':
            conv.send_message_bus_release(msg_data, 'current', False)
        else:
            conv.block_conversation()
            conv.send_message_bus_release(msg_data, 'done')
        ret = env['acrux.chat.bot']
except Exception as e:
    conv = mess_id.conversation_id
    msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'Error'}
    back = conv.status
    if back == 'current':
        conv.send_message_bus_release(msg_data, 'current', False)
    else:
        conv.block_conversation()
        conv.send_message_bus_release(msg_data, 'done')
    ret = env['acrux.chat.bot']
'''

old_ret = "            ret = [{'send_text': msg}]"
print(f'old_ret found: {old_ret in code}')
for i, line in enumerate(code.split('\n')):
    if 'ret = [{' in line:
        print(f'Line {i+1}: {repr(line)}')
    if line == old_ret:
        print(f'  ^ exact match at line {i+1}')

# Also check what the old line actually is
print()
print('Now checking the exact bytes around the match...')
for i, line in enumerate(code.split('\n')):
    if 'ret' in line:
        print(f'{i+1}: len={len(line)}, repr={repr(line)}')
