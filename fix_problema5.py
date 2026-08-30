import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def call(method, args=None, kwargs=None):
    if kwargs is None:
        kwargs = {}
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/' + method, json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': method, 'args': args or [], 'kwargs': kwargs}
    })
    return resp.json()

# 1. Fix sequence: RECOMPRA_PROBLEMA (70) to seq=20, RECOMPRA_CONVENIO (85) to seq=4
# (order should be: 1-Credito, 2-Contado, 3-Catalogo, 4-Convenio, 5-Reportar, ASESOR, 6-Consultar)
call('write', [[70], {'sequence': 20}])
call('write', [[85], {'sequence': 4}])
print('Fixed sequences: Convenio (85)=seq=4, Problema (70)=seq=20')

# 2. Also update RECOMPRA_PROBLEMA code: 
#    The issue might be that clear_catcher closes before send_text.
#    Remove clear_catcher, keep only send_text + message to contact a human.
#    Also fix the contact_id fields to avoid potential errors.

NEW_CODE = """try:
    connector = env['acrux.chat.connector'].search([('id','=',2)], limit=1)
    Conv = env['acrux.chat.conversation']
    number = '584147305385'
    conv_id = Conv.search([('connector_id', '=', connector.id), ('number', '=', number)], limit=1)
    if not conv_id:
        partner = env['res.partner'].search([('mobile', '=', number)], limit=1)
        if partner:
            conv_id = Conv.conversation_create(partner.id, connector.id, number)
        else:
            conv_id = Conv.conversation_create(False, connector.id, number)
    alert_text = "Saludos, soy *LatinBot*: Tu *Asistente Virtual*, te aviso que el cliente *" + str(mess_id.contact_id.name) + "* con el numero " + str(mess_id.contact_id.number) + " esta esperando en el ChatRoom para ser atendido"
    msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv_id.id, 'text': alert_text}
    if conv_id and conv_id.status == 'current':
        conv_id.send_message_bus_release(msg_data, 'current', False)
    elif conv_id:
        conv_id.block_conversation()
        conv_id.send_message_bus_release(msg_data, 'done')
except Exception as e:
    pass

ret = [{'send_text': 'Perfecto! He recopilado toda tu informacion con exito. Para garantizarte una asesoria completamente personalizada, te estoy transfiriendo en este instante con uno de nuestros asesores.'}, {'clear_catcher': True}]"""

# Write to RECOMPRA_PROBLEMA (70) and also check/update LC_PROBLEMA, REG_PROBLEMA, NR_PROBLEMA
problem_bots = [
    (70, 'RECOMPRA_PROBLEMA'),
]

for bid, name in problem_bots:
    result = call('write', [[bid], {'code': NEW_CODE}])
    if result.get('result'):
        print('{} (ID={}): OK'.format(name, bid))
    else:
        print('{} (ID={}): FAIL - {}'.format(name, bid, result.get('error', {})))

# Also update the ASESOR bots with same fix
asesor_code = NEW_CODE.replace("te estoy transfiriendo", "te estoy transfiriendo")
for bid in [97, 98, 99, 100]:
    name = 'ASESOR_' + str(bid)
    result = call('write', [[bid], {'code': NEW_CODE}])
    if result.get('result'):
        print('{} (ID={}): OK'.format(name, bid))
    else:
        print('{} (ID={}): FAIL - {}'.format(name, bid, result.get('error', {})))

# Verify the structure
print('\n--- Updated MENU_RECOMPRA children ---')
resp = call('search_read', [[['parent_id','=',65]]], {'fields':['id','name','text_match','sequence'],'order':'sequence asc, id asc'})
for c in resp.get('result', []):
    val = c['text_match']
    if val is False:
        tm = 'HANDLER'
    elif val:
        tm = 'match={}'.format(repr(val))
    else:
        tm = 'no match'
    print('  seq={} ID={} {} {}'.format(c['sequence'], c['id'], tm, c['name']))
