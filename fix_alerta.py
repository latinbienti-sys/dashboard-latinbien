import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# ---------------------------------------------------------------------------
# CODIGO DE ALERTA + TRANSFERENCIA (reutilizable)
# ---------------------------------------------------------------------------
ALERT_CODE = """
try:
    connector = env['acrux.chat.connector'].search([('id','=',2)], limit=1)
    Conv = env['acrux.chat.conversation']
    number = '584147305385'
    conv_id = Conv.search([('connector_id', '=', connector.id), ('number', '=', number)], limit=1)
    if not conv_id:
        partner = env['res.partner'].search([('mobile', '=', number)], limit=1)
        conv_id = Conv.conversation_create(partner, connector.id, number)
    alert_text = "Saludos, soy *LatinBot*: Tu *Asistente Virtual*, te aviso que el cliente *" + mess_id.contact_id.name + "* con el numero " + mess_id.contact_id.number + " esta esperando en el ChatRoom para ser atendido"
    msg_data = {'ttype': 'text', 'from_me': True, 'contact_id': conv_id.id, 'text': alert_text}
    if conv_id.status == 'current':
        conv_id.send_message_bus_release(msg_data, 'current', False)
    else:
        conv_id.block_conversation()
        conv_id.send_message_bus_release(msg_data, 'done')
except:
    pass

ret = [{'send_text': 'Perfecto! He recopilado toda tu informacion con exito. Para garantizarte una asesoria completamente personalizada, te estoy transfiriendo en este instante con uno de nuestro asesores.'}, {'clear_catcher': True}]
"""

# ---------------------------------------------------------------------------
# Bots a ACTUALIZAR con alerta
# ---------------------------------------------------------------------------
BOTS_ALERTA = [
    # (bot_id, nombre)
    (68, 'RECOMPRA_CREDITO'),
    (72, 'LC_SOLICITAR_CREDITO'),
    (70, 'RECOMPRA_PROBLEMA'),
    (75, 'LC_PROBLEMA'),
    (96, 'REG_PROBLEMA'),
    (83, 'NR_PROBLEMA'),
]

print('=== ACTUALIZANDO BOTS EXISTENTES ===')
for bot_id, name in BOTS_ALERTA:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {
            'model': 'acrux.chat.bot',
            'method': 'write',
            'args': [[bot_id], {
                'code': ALERT_CODE,
                'body_whatsapp': False
            }],
            'kwargs': {}
        }
    })
    result = resp.json()
    if result.get('result') == True:
        print(f'  {bot_id} {name} -> OK')
    else:
        print(f'  {bot_id} {name} -> ERROR: {result.get("error",{}).get("message","???")}')

# ---------------------------------------------------------------------------
# Crear bots "ASESOR" en cada menú
# ---------------------------------------------------------------------------
# Primero obtener los bot_key de los menus
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['id', 'in', [65, 66, 64, 63]]]],
        'kwargs': {'fields': ['id', 'name', 'bot_key']}
    }
})
menus = resp.json().get('result', [])

ASESOR_BOTS = [
    {'parent_id': 65, 'name': 'RECOMPRA_ASESOR', 'menu_key': '#MENU_RECOMPRA'},
    {'parent_id': 66, 'name': 'LC_ASESOR', 'menu_key': '#MENU_LC_APROBADA'},
    {'parent_id': 64, 'name': 'REG_ASESOR', 'menu_key': '#No tienes linea'},
    {'parent_id': 63, 'name': 'NR_ASESOR', 'menu_key': '#Registro'},
]

print('\n=== CREANDO BOTS ASESOR ===')
for bot_info in ASESOR_BOTS:
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/create', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {
            'model': 'acrux.chat.bot',
            'method': 'create',
            'args': [{
                'name': bot_info['name'],
                'parent_id': bot_info['parent_id'],
                'text_match': 'ASESOR',
                'code': ALERT_CODE,
                'body_whatsapp': False,
                'active': True,
            }],
            'kwargs': {}
        }
    })
    result = resp.json()
    new_id = result.get('result')
    if new_id:
        print(f'  CREADO {bot_info["name"]} (ID={new_id}) bajo parent_id={bot_info["parent_id"]}')
    else:
        print(f'  ERROR {bot_info["name"]}: {result.get("error",{}).get("message","???")}')

# ---------------------------------------------------------------------------
# Verificar los cambios
# ---------------------------------------------------------------------------
print('\n=== VERIFICACION ===')
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['id', 'in', [68, 72, 70, 75, 96, 83]]]],
        'kwargs': {'fields': ['id', 'name', 'text_match']}
    }
})
for b in resp.json().get('result', []):
    print(f'  {b["id"]} {b["name"]} text_match={b["text_match"]}')

print('\n=== NUEVOS BOTS ASESOR ===')
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['name', 'like', '%ASESOR%'], ['parent_id', 'not in', [False]]]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'parent_id']}
    }
})
for b in resp.json().get('result', []):
    pid = b.get('parent_id', ['',''])
    print(f'  {b["id"]} {b["name"]} text_match={b["text_match"]} parent={pid[1] if isinstance(pid, list) else pid}')

print('\n=== LISTO ===')
