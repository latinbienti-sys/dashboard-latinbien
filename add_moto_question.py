# -*- coding: utf-8 -*-
# REHACE el catcher de moto como PREGUNTA PROACTIVA (no por keyword).
# 130 (hijo de 61) pregunta "¿Deseas información sobre las motos?".
# 131 #MOTO_MENU (contenedor) -> 133 #MOTO_BRANCH (handler):
#   - SÍ / moto / quiero -> muestra menu de opciones.
#   - rama (requisitos/catalogo/seguimiento/entrega/ubicacion o 1-5) -> responde y se queda en modo moto.
#   - NO / salir / comercial -> goto #VALIDAR_CEDULA (flujo normal, sin re-preguntar).
# Elimina los bots 126-129 (campaña vieja por keyword en menús).
import requests, sys, json
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)
s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
API = 'https://latinbien.com/web/dataset/call_kw'
def call(model, method, args, kwargs=None):
    r = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    j = r.json()
    if 'error' in j:
        print('   !! API ERROR:', j['error'].get('message'), '|', str(j['error'].get('data', ''))[:200])
    return j.get('result')

# --- Respuestas ---
resp_pregunta = (
    "\U0001F3CD\ufe0f \u00bfDeseas informaci\u00f3n sobre las motos de Latinbien? "
    "Responde S\u00cd para ver las opciones o NO para la atenci\u00f3n comercial habitual."
)
resp_requisitos = (
    "\U0001F4CC Documentos para tu Cr\u00e9diMoto:\n"
    "\U0001F4C4 Identificaci\u00f3n: C\u00e9dula, RIF, Licencia (2da), Certificado M\u00e9dico y Recibo de servicio.\n"
    "\U0001F4B3 Perfil Financiero: Movimientos bancarios (\u00faltimos 3 meses, m\u00edn. 2 bancos), referencia bancaria y giro. "
    "(Si usas plataformas/cuentas en divisas, adj\u00fantalas para fortalecer la aprobaci\u00f3n).\n"
    "\U0001F4DE Contactos: 2 referencias personales, 2 familiares y RCV.\n"
    "\U0001F52E \u00bfNecesitas Avalista?: Aplica solo si la moto supera $1.500, si eres profesional independiente o tienes entre 18 y 21 a\u00f1os."
)
resp_catalogo = (
    "\U0001F973 \u00a1Estrenar tu moto en Latinbien es muy simple!\n"
    "El proceso: Aprobamos tu cr\u00e9dito \u27a1\ufe0f Pagas inicial \u27a1\ufe0f Te llevas tu moto (hasta 10 meses de plazo). "
    "Todos los montos se calculan en bol\u00edvares a la tasa oficial BCV del d\u00eda y aceptamos todos los m\u00e9todos de pago.\n"
    "\U0001F4F2 Explora los modelos en nuestro Cat\u00e1logo Digital de Motos."
)
resp_seguimiento = (
    "\u00a1No te preocupes! \U0001F64C \u00bfPara qu\u00e9 fecha calculas tener lista tu inicial?\n"
    "Con ese dato te programo una llamada de seguimiento para avanzar con los recaudos en el momento preciso. "
    "\u00a1Porque puedes y te lo mereces! \U0001F4F2"
)
resp_entrega = (
    "\U0001F3CD\ufe0f\U0001F4A8 \u00a1Superr\u00e1pido! Tan pronto como tu l\u00ednea de cr\u00e9dito sea aprobada y se registre el pago de la inicial, "
    "te hacemos la entrega en un m\u00e1ximo de 2 d\u00edas h\u00e1biles.\n"
    "Si ya tienes el modelo definido, \u00bfte gustar\u00eda que te enviemos la lista de recaudos para formalizar tu solicitud hoy mismo?"
)
resp_ubicacion = (
    "\U0001F4CD Estamos ubicados en:\n"
    "Avenida Las Am\u00e9ricas\n"
    "Centro Comercial Rodeo Plaza\n"
    "Nivel 1 Local N1-12"
)
resp_menu = (
    "\U0001F3CD\ufe0f *Opciones Cr\u00e9diMoto Latinbien:*\n"
    "1\ufe0f\u20e3 Requisitos y recaudos\n"
    "2\ufe0f\u20e3 Cat\u00e1logo y modelos\n"
    "3\ufe0f\u20e3 Seguimiento (a\u00fan sin inicial)\n"
    "4\ufe0f\u20e3 Tiempos de entrega\n"
    "5\ufe0f\u20e3 Ubicaci\u00f3n y horario\n"
    "Escribe el n\u00famero o la palabra de tu inter\u00e9s. Si prefieres la atenci\u00f3n comercial normal, escribe NO."
)
FOOT = "\n\n(\u00bfAlgo m\u00e1s? Escribe NO para ir a la atenci\u00f3n comercial.)"

# --- Codigo del handler (bots 131 y 133) ---
HANDLER = r'''texto = (mess_id.text or '').strip().lower()
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
                      + str(mess_id.contact_id.name) + "* con el n\u00famero "
                      + str(mess_id.contact_id.number)
                      + " solicito asesoria (Cr\u00e9diMoto) y prefiere ser atendido por un asesor.")
        msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv_id.id, 'text': alert_text}
        if conv_id and conv_id.status == 'current':
            conv_id.send_message_bus_release(msg_data, 'current', False)
        elif conv_id:
            conv_id.block_conversation()
            conv_id.send_message_bus_release(msg_data, 'done')
    except Exception:
        pass
    return [{'send_text': "\U0001F60A Pronto ser\u00e1s atendido por uno de nuestros asesores. Te contactaremos a la brevedad."}]
def _menu():
    return [{'send_text': __RESP_MENU__, 'goto_and_wait': '#MOTO_MENU'}]
if mess_id.ttype != 'text' or not texto:
    ret = [{'goto_and_wait': '#MOTO_MENU'}]
elif ('salir' in texto) or ('volver' in texto) or ('comercial' in texto):
    ret = _salir()
elif ('menu' in texto):
    ret = _menu()
elif (texto in ('1','1.')) or ('recaud' in texto) or ('requisit' in texto) or ('document' in texto) or ('necesito' in texto) or ('aval' in texto) or ('credito' in texto):
    ret = [{'send_text': __RESP_REQUISITOS__ + __FOOT__, 'goto_and_wait': '#MOTO_MENU'}]
elif (texto in ('2','2.')) or ('catalog' in texto) or ('model' in texto) or ('precio' in texto) or ('cotiz' in texto):
    ret = [{'send_text': __RESP_CATALOGO__ + __FOOT__, 'goto_and_wait': '#MOTO_MENU'}]
elif (texto in ('3','3.')) or ('no teng' in texto) or ('no me alcanz' in texto) or ('sin inicial' in texto) or ('luego' in texto) or ('aun no' in texto) or ('todavia no' in texto) or ('no cuent' in texto):
    ret = [{'send_text': __RESP_SEGUIMIENTO__ + __FOOT__, 'goto_and_wait': '#MOTO_MENU'}]
elif (texto in ('4','4.')) or ('cuanto tard' in texto) or ('tiempo de entreg' in texto) or ('cuando' in texto) or ('entreg' in texto) or ('demora' in texto) or ('dias hab' in texto):
    ret = [{'send_text': __RESP_ENTREGA__ + __FOOT__, 'goto_and_wait': '#MOTO_MENU'}]
elif (texto in ('5','5.')) or ('ubicac' in texto) or ('direcc' in texto) or ('donde' in texto) or ('rodeo' in texto) or ('local' in texto) or ('sucursal' in texto):
    ret = [{'send_text': __RESP_UBICACION__ + __FOOT__, 'goto_and_wait': '#MOTO_MENU'}]
elif ('no' in texto) or ('nada' in texto) or ('nop' in texto) or ('ningun' in texto):
    ret = _salir()
else:
    ret = _menu()
'''

# --- C\u00f3digo del pregunt\u00f3n (bot 130) ---
PREGUNTA = r'''texto = (mess_id.text or '').strip().lower()
if mess_id.ttype != 'text' or not texto:
    ret = [{'next': True}]
else:
    ret = [{'send_text': __RESP_PREGUNTA__, 'goto_and_wait': '#MOTO_MENU'}]
'''

def build(code):
    code = code.replace('__RESP_PREGUNTA__', json.dumps(resp_pregunta))
    code = code.replace('__RESP_MENU__', json.dumps(resp_menu))
    code = code.replace('__RESP_REQUISITOS__', json.dumps(resp_requisitos))
    code = code.replace('__RESP_CATALOGO__', json.dumps(resp_catalogo))
    code = code.replace('__RESP_SEGUIMIENTO__', json.dumps(resp_seguimiento))
    code = code.replace('__RESP_ENTREGA__', json.dumps(resp_entrega))
    code = code.replace('__RESP_UBICACION__', json.dumps(resp_ubicacion))
    code = code.replace('__FOOT__', json.dumps(FOOT))
    return code

handler_code = build(HANDLER)
pregunta_code = build(PREGUNTA)
for name, c in [('PREGUNTA', pregunta_code), ('HANDLER', handler_code)]:
    try:
        compile(c, name, 'exec')
    except SyntaxError as e:
        print('\u274c SYNTAX', name, e); sys.exit(1)

# Confirmar root 61
r = call('acrux.chat.bot', 'read', [[61]], {'fields': ['id','name','bot_key','child_ids']})
print('Root:', r[0]['name'], 'hijos=', r[0]['child_ids'])

def get_id_by_key(key):
    res = call('acrux.chat.bot', 'search_read', [[('bot_key', '=', key)]], {'fields': ['id']})
    return res[0]['id'] if res else None

# 1) #MOTO_MENU (131) - reusar si existe
id131 = get_id_by_key('#MOTO_MENU')
if not id131:
    id131 = call('acrux.chat.bot', 'create', [{
        'name': 'MOTO_MENU (CONECTOR COMERCIAL)', 'connector_id': 2, 'parent_id': 130,
        'text_match': False, 'bot_key': '#MOTO_MENU', 'code': handler_code, 'sequence': 1, 'active': True}])
    print(f'\u2705 creado #MOTO_MENU = {id131}')
else:
    call('acrux.chat.bot', 'write', [[id131], {'parent_id': 130, 'text_match': False,
        'bot_key': '#MOTO_MENU', 'code': handler_code, 'sequence': 1, 'active': True}])
    print(f'\u2705 reutilizado #MOTO_MENU = {id131}')

# 2) #MOTO_BRANCH (133) hijo de 131 - reusar si existe
id133 = get_id_by_key('#MOTO_BRANCH')
if not id133:
    id133 = call('acrux.chat.bot', 'create', [{
        'name': 'MOTO_BRANCH (CONECTOR COMERCIAL)', 'connector_id': 2, 'parent_id': id131,
        'text_match': False, 'bot_key': '#MOTO_BRANCH', 'code': handler_code, 'sequence': 1, 'active': True}])
    print(f'\u2705 creado #MOTO_BRANCH = {id133}')
else:
    call('acrux.chat.bot', 'write', [[id133], {'parent_id': id131, 'text_match': False,
        'bot_key': '#MOTO_BRANCH', 'code': handler_code, 'sequence': 1, 'active': True}])
    print(f'\u2705 reutilizado #MOTO_BRANCH = {id133}')

if not (id131 and id133):
    print('\u274c no se pudieron crear 131/133'); sys.exit(1)

# 3) Reusar/actualizar bot 130: pregunta proactiva, hijo de 61, seq 1
id130 = get_id_by_key('#MOTO_CATCHER_61')
if not id130:
    id130 = call('acrux.chat.bot', 'create', [{
        'name': 'MOTO_CATCHER_COMERCIAL', 'connector_id': 2, 'parent_id': 61,
        'text_match': False, 'bot_key': '#MOTO_CATCHER_61', 'code': pregunta_code,
        'sequence': 1, 'active': True}])
    print(f'\u2705 creado #MOTO_CATCHER_61 = {id130}')
else:
    call('acrux.chat.bot', 'write', [[id130], {'parent_id': 61, 'text_match': False,
        'bot_key': '#MOTO_CATCHER_61', 'code': pregunta_code, 'sequence': 1, 'active': True}])
    print(f'\u2705 reutilizado #MOTO_CATCHER_61 = {id130}')

# 4) Eliminar bots viejos 126-129 (campaña por keyword en menús)
old = call('acrux.chat.bot', 'search_read', [[('bot_key', 'in', ['#MOTO_CAMPANA_65','#MOTO_CAMPANA_66','#MOTO_CAMPANA_64','#MOTO_CAMPANA_63'])]], {'fields': ['id','name']})
if old:
    ids = [b['id'] for b in old]
    call('acrux.chat.bot', 'unlink', [ids])
    print(f'\u2705 eliminados bots viejos: {ids}')
else:
    print('(no habia bots 126-129 que eliminar)')

# 5) Verificacion de arbol
print('\n=== Arbol moto ===')
tree = call('acrux.chat.bot', 'read', [[id130, id131, id133]], {'fields': ['id','name','parent_id','bot_key','child_ids','sequence']})
for b in tree:
    print(f"  [{b['id']}] {b['name']} parent={b['parent_id'][0] if b['parent_id'] else None} key={b['bot_key']} hijos={b['child_ids']}")

# 6) Simulacion del handler (respuestas del cliente)
print('\n=== Simulacion handler moto ===')
def sim(txt):
    t = txt.strip().lower()
    if ('salir' in t) or ('volver' in t) or ('comercial' in t): return 'SALIR->#VALIDAR_CEDULA'
    if ('menu' in t): return 'MENU'
    if (t in ('1','1.')) or ('recaud' in t) or ('requisit' in t) or ('document' in t) or ('necesito' in t) or ('aval' in t) or ('credito' in t): return 'REQUISITOS'
    if (t in ('2','2.')) or ('catalog' in t) or ('model' in t) or ('precio' in t) or ('cotiz' in t): return 'CATALOGO'
    if (t in ('3','3.')) or ('no teng' in t) or ('no me alcanz' in t) or ('sin inicial' in t) or ('luego' in t) or ('aun no' in t) or ('todavia no' in t) or ('no cuent' in t): return 'SEGUIMIENTO'
    if (t in ('4','4.')) or ('cuanto tard' in t) or ('tiempo de entreg' in t) or ('cuando' in t) or ('entreg' in t) or ('demora' in t) or ('dias hab' in t): return 'ENTREGA'
    if (t in ('5','5.')) or ('ubicac' in t) or ('direcc' in t) or ('donde' in t) or ('rodeo' in t) or ('local' in t) or ('sucursal' in t): return 'UBICACION'
    if ('no' in t) or ('nada' in t) or ('nop' in t) or ('ningun' in t): return 'SALIR->#VALIDAR_CEDULA'
    return 'MENU (por defecto)'
for txt in ['si','sí','quiero moto','1','requisitos','2','catalogo','no tengo inicial','3','cuanto tardan','4','donde quedan','5','no','no gracias','salir','menu','hola']:
    print(f"  resp={txt!r:22} -> {sim(txt)}")
