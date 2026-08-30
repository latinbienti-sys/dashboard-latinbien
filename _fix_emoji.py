import requests, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s=requests.Session(); s.headers.update({'Content-Type':'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
def call(model,method,args,kwargs=None):
    r=s.post(f'https://latinbien.com/web/dataset/call_kw/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    j=r.json()
    if 'error' in j: print('   ERR', j['error'].get('message'), str(j['error'].get('data',''))[:200]); return None
    return j.get('result')

question_code = r"""texto = (mess_id.text or '').strip().lower()
if mess_id.ttype != 'text' or not texto:
    ret = [{'next': True}]
else:
    ret = [{'send_text': "¿Deseas informacion sobre las motos de Latinbien? Responde SI para ver las opciones o NO para la atencion comercial habitual.", 'goto_and_wait': '#MOTO_MENU'}]
"""

handler_code = r"""texto = (mess_id.text or '').strip().lower()

def _salir():
    # Avisar al asesor (numero 424-7035927 => 584247035927) y decirle al cliente que sera atendido.
    # NO se pide validar cedula.
    try:
        connector = env['acrux.chat.connector'].search([('id', '=', 2)], limit=1)
        Conv = env['acrux.chat.conversation']
        number = '584247035927'
        conv_id = Conv.search([('connector_id', '=', connector.id), ('number', '=', number)], limit=1)
        if not conv_id:
            partner = env['res.partner'].search([('mobile', '=', number)], limit=1)
            if partner:
                conv_id = Conv.conversation_create(partner.id, connector.id, number)
            else:
                conv_id = Conv.conversation_create(False, connector.id, number)
        alert_text = ("Saludos, soy *LatinBot*: Tu *Asistente Virtual*, te aviso que el cliente *"
                      + str(mess_id.contact_id.name) + "* con el numero "
                      + str(mess_id.contact_id.number)
                      + " solicito asesoria (CreDiMoto) y prefiere ser atendido por un asesor.")
        msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv_id.id, 'text': alert_text}
        if conv_id and conv_id.status == 'current':
            conv_id.send_message_bus_release(msg_data, 'current', False)
        elif conv_id:
            conv_id.block_conversation()
            conv_id.send_message_bus_release(msg_data, 'done')
    except Exception:
        pass
    return [{'send_text': "Pronto seras atendido por uno de nuestros asesores. Te contactaremos a la brevedad."}]

def _menu():
    return [{'send_text': "*Opciones de motos Latinbien:*\n1. Requisitos y recaudos\n2. Catalogo y modelos\n3. Seguimiento (aun sin inicial)\n4. Tiempos de entrega\n5. Ubicacion y horario\nEscribe el numero o la palabra de tu interes. Si prefieres la atencion comercial normal, escribe NO.", 'goto_and_wait': '#MOTO_MENU'}]

if mess_id.ttype != 'text' or not texto:
    ret = [{'goto_and_wait': '#MOTO_MENU'}]
elif ('salir' in texto) or ('volver' in texto) or ('comercial' in texto):
    ret = _salir()
elif ('menu' in texto):
    ret = _menu()
elif (texto in ('1','1.')) or ('recaud' in texto) or ('requisit' in texto) or ('document' in texto) or ('necesito' in texto) or ('aval' in texto) or ('credito' in texto):
    ret = [{'send_text': "Documentos para tu moto en Latinbien:\n- Identificacion: Cedula, RIF, Licencia (2da), Certificado Medico y Recibo de servicio.\n- Perfil Financiero: Movimientos bancarios (ultimos 3 meses, min. 2 bancos), referencia bancaria y giro. (Si usas plataformas/cuentas en divisas, adjuntalas para fortalecer la aprobacion).\n- Contactos: 2 referencias personales, 2 familiares y RCV.\n- ¿Necesitas Avalista?: Aplica solo si la moto supera $1.500, si eres profesional independiente o tienes entre 18 y 21 anos.\n\n(¿Algo mas? Escribe NO para ir a la atencion comercial.)", 'goto_and_wait': '#MOTO_MENU'}]
elif (texto in ('2','2.')) or ('catalog' in texto) or ('model' in texto) or ('precio' in texto) or ('cotiz' in texto):
    ret = [{'send_text': "¡Estrenar tu moto en Latinbien es muy simple!\nEl proceso: Aprobamos tu credito -> Pagas inicial -> Te llevas tu moto (hasta 10 meses de plazo). Todos los montos se calculan en bolivares a la tasa oficial BCV del dia y aceptamos todos los metodos de pago.\nExplora los modelos en nuestro Catalogo Digital de Motos.\n\n(¿Algo mas? Escribe NO para ir a la atencion comercial.)", 'goto_and_wait': '#MOTO_MENU'}]
elif (texto in ('3','3.')) or ('no teng' in texto) or ('no me alcanz' in texto) or ('sin inicial' in texto) or ('luego' in texto) or ('aun no' in texto) or ('todavia no' in texto) or ('no cuent' in texto):
    ret = [{'send_text': "No te preocupes! ¿Para que fecha calculas tener lista tu inicial?\nCon ese dato te programo una llamada de seguimiento para avanzar con los recaudos en el momento preciso. ¡Porque puedes y te lo mereces!\n\n(¿Algo mas? Escribe NO para ir a la atencion comercial.)", 'goto_and_wait': '#MOTO_MENU'}]
elif (texto in ('4','4.')) or ('cuanto tard' in texto) or ('tiempo de entreg' in texto) or ('cuando' in texto) or ('entreg' in texto) or ('demora' in texto) or ('dias hab' in texto):
    ret = [{'send_text': "¡Superrapido! Tan pronto como tu linea de credito sea aprobada y se registre el pago de la inicial, te hacemos la entrega en un maximo de 2 dias habiles.\nSi ya tienes el modelo definido, ¿te gustaria que te enviemos la lista de recaudos para formalizar tu solicitud hoy mismo?\n\n(¿Algo mas? Escribe NO para ir a la atencion comercial.)", 'goto_and_wait': '#MOTO_MENU'}]
elif (texto in ('5','5.')) or ('ubicac' in texto) or ('direcc' in texto) or ('donde' in texto) or ('rodeo' in texto) or ('local' in texto) or ('sucursal' in texto):
    ret = [{'send_text': "Estamos ubicados en:\nAvenida Las Americas\nCentro Comercial Rodeo Plaza\nNivel 1 Local N1-12\n\n(¿Algo mas? Escribe NO para ir a la atencion comercial.)", 'goto_and_wait': '#MOTO_MENU'}]
elif ('no' in texto) or ('nada' in texto) or ('nop' in texto) or ('ningun' in texto):
    ret = _salir()
else:
    ret = _menu()
"""

# Local check: ensure no astral (surrogate) chars anywhere in outgoing text
def has_astral(s):
    return any(ord(c) > 0xFFFF for c in s)

for bid, code in [(130, question_code), (131, handler_code), (134, handler_code)]:
    # verify the code executes and produces BMP-only send_text
    local = {'env': None, 'mess_id': type('M', (), {'text': 'hola', 'ttype': 'text', 'contact_id': type('C', (), {'name':'X','number':'0'})()})()}
    try:
        exec(code, local)
        ret = local.get('ret', [])
        bad = [r for r in ret if 'send_text' in r and has_astral(r['send_text'])]
        if bad:
            print(f"bot {bid}: STILL HAS ASTRAL EMOJI -> {[r['send_text'][:20] for r in bad]}")
        else:
            print(f"bot {bid}: local eval OK, send_text BMP-only ({len(ret)} branch(es))")
    except Exception as e:
        print(f"bot {bid}: LOCAL EVAL ERROR {e}")
    # push to Odoo
    res = call('acrux.chat.bot','write',[[bid],{'code': code}])
    print(f"bot {bid}: write -> {res}")
