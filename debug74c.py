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

indent = '            '
var_expr = 'msg'
lines_out = []
lines_out.append(f'{indent}conv = mess_id.conversation_id')
lines_out.append(f"{indent}msg_data = {{'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': {var_expr}}}")
lines_out.append(f'{indent}back = conv.status')
lines_out.append(f"{indent}if back == 'current':")
lines_out.append(f"{indent}    conv.send_message_bus_release(msg_data, 'current', False)")
lines_out.append(f'{indent}else:')
lines_out.append(f'{indent}    conv.block_conversation()')
lines_out.append(f"{indent}    conv.send_message_bus_release(msg_data, 'done')")
lines_out.append(f"{indent}ret = env['acrux.chat.bot']")
replacement = '\n'.join(lines_out)

old_ret = "            ret = [{'send_text': msg}]"
new_code = code.replace(old_ret, replacement)

print("=== New code ===")
for i, line in enumerate(new_code.split('\n')):
    print(f'{i+1}: {repr(line)}')

print()
print("=== Compile test ===")
try:
    compile(new_code, '<string>', 'exec')
    print("SUCCESS - compiles OK")
except SyntaxError as e:
    print(f"ERROR L{e.lineno}: {e.msg}")
