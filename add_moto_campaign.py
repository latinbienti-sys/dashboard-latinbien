# -*- coding: utf-8 -*-
# AGREGA CAMPANA CREDIMOTO (conector 2 comercial) SIN TOCAR LO EXISTENTE.
# Crea 1 bot hijo (catch-all, tm=False) por cada menu, con sequence BAJO para
# evaluarse ANTES que los buscadores de precio. Si detecta keyword de moto ->
# responde y se queda en el menu (goto_and_wait). Si NO -> {'next': True} para
# que el buscador de precio existente funcione igual que antes (no se afecta).
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
    return r.json().get('result')

# ---- Mensajes de la campana (texto informativo) ----
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
    "\U0001F4F2 Explora los modelos en nuestro Cat\u00e1logo Digital de Motos.\n"
    "Cu\u00e9ntame para sugerirte el plan ideal:\n"
    "\u00bfPara qu\u00e9 uso la necesitas? (Personal / Trabajo)\n"
    "\u00bfCon qu\u00e9 monto estimado cuentas para la inicial?"
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

BODY = r'''texto = (mess_id.text or '').strip().lower()
if mess_id.ttype != 'text' or not texto:
    ret = [{'next': True}]
else:
    is_moto = ('moto' in texto) or ('motos' in texto) or ('creditomoto' in texto) or ('credito moto' in texto) or ('moto latinbien' in texto)
    if not is_moto:
        ret = [{'next': True}]
    else:
        menu_key = __MENU_KEY__
        resp_requisitos = __RESP_REQUISITOS__
        resp_catalogo = __RESP_CATALOGO__
        resp_seguimiento = __RESP_SEGUIMIENTO__
        resp_entrega = __RESP_ENTREGA__
        resp_ubicacion = __RESP_UBICACION__
        if ('recaud' in texto) or ('requisit' in texto) or ('document' in texto) or ('necesito' in texto) or ('aval' in texto) or ('credito' in texto):
            msg = resp_requisitos
        elif ('no teng' in texto) or ('no me alcanz' in texto) or ('sin inicial' in texto) or ('luego' in texto) or ('aun no' in texto) or ('todavia no' in texto) or ('no cuent' in texto):
            msg = resp_seguimiento
        elif ('cuanto tard' in texto) or ('tiempo de entreg' in texto) or ('cuando' in texto) or ('entreg' in texto) or ('demora' in texto) or ('dias hab' in texto):
            msg = resp_entrega
        elif ('ubicac' in texto) or ('direcc' in texto) or ('donde' in texto) or ('rodeo' in texto) or ('local' in texto) or ('sucursal' in texto):
            msg = resp_ubicacion
        else:
            msg = resp_catalogo
        ret = [{'send_text': msg, 'goto_and_wait': menu_key}]
'''

def build_code(menu_key):
    code = BODY
    code = code.replace('__MENU_KEY__', json.dumps(menu_key))
    code = code.replace('__RESP_REQUISITOS__', json.dumps(resp_requisitos))
    code = code.replace('__RESP_CATALOGO__', json.dumps(resp_catalogo))
    code = code.replace('__RESP_SEGUIMIENTO__', json.dumps(resp_seguimiento))
    code = code.replace('__RESP_ENTREGA__', json.dumps(resp_entrega))
    code = code.replace('__RESP_UBICACION__', json.dumps(resp_ubicacion))
    return code

# menus destino: (menu_id, bot_key_del_menu, nombre, bot_key_nuevo)
MENUS = [
    (65, '#MENU_RECOMPRA',      'MOTO_CAMPANA_RECOMPRA',  '#MOTO_CAMPANA_65'),
    (66, '#MENU_LC_APROBADA',   'MOTO_CAMPANA_LC',        '#MOTO_CAMPANA_66'),
    (64, '#No tienes linea',    'MOTO_CAMPANA_REGISTRADO','#MOTO_CAMPANA_64'),
    (63, '#Registro',           'MOTO_CAMPANA_NOREG',     '#MOTO_CAMPANA_63'),
]

# 1) Verificar que los bot_key destino existen (tienen hijos) antes de crear
print('=== Verificacion de bot_key destino ===')
for mid, mkey, _, _ in MENUS:
    r = call('acrux.chat.bot', 'search_read', [[('bot_key', '=', mkey)]], {'fields': ['id', 'name', 'child_ids']})
    ok = bool(r) and len(r[0].get('child_ids') or []) > 0
    print(f"  menu {mkey}: {'OK' if ok else 'FALTA'} {r and r[0].get('id')}")

print('\n=== Creacion de bots de campana (catch-all, tm=False, sequence bajo) ===')
created = []
for mid, mkey, name, bkey in MENUS:
    code = build_code(mkey)
    try:
        compile(code, '<moto>', 'exec')
    except SyntaxError as e:
        print(f'  \u274c SYNTAX {name}: {e}')
        continue
    new_id = call('acrux.chat.bot', 'create', [{
        'name': name,
        'connector_id': 2,
        'parent_id': mid,
        'text_match': False,
        'bot_key': bkey,
        'code': code,
        'sequence': 1,
        'active': True,
    }])
    if not new_id:
        print(f'  \u274c create fallo {name}')
        continue
    # Forzar sequence bajo para quedar ANTES que los buscadores de precio (tm=False)
    call('acrux.chat.bot', 'write', [[new_id], {'sequence': 1}])
    created.append((new_id, mid, name, mkey))
    print(f'  \u2705 Bot {new_id} ({name}) creado en menu {mid} ({mkey})')

print('\n=== VERIFICACION FINAL: orden de hijos por menu ===')
for mid, mkey, name, bkey in MENUS:
    kids = call('acrux.chat.bot', 'search_read', [[('parent_id', '=', mid)]],
                {'fields': ['id', 'name', 'text_match', 'sequence', 'bot_key'], 'order': 'sequence'})
    nomatch = [k for k in kids if not k.get('text_match')]
    print(f"\n  Menu {mid} ({mkey}) - catch-alls (tm=False) en orden seq:")
    for k in nomatch:
        mark = '  <-- MOTO' if k['bot_key'] == bkey else ''
        print(f"    [{k['id']}] seq={k['sequence']} {k['name']}{mark}")
    # Confirmar que el bot moto queda antes que los buscadores de precio
    ids_nm = [k['id'] for k in nomatch]
    moto_bot = next((k for k in nomatch if k['bot_key'] == bkey), None)
    if moto_bot:
        precio_bots = [k['id'] for k in nomatch if k['bot_key'] != bkey]
        before = all(ids_nm.index(moto_bot['id']) < ids_nm.index(p) for p in precio_bots)
        mark = '\u2705' if before else '\u274c REVISAR'
        print("    => Moto bot primero entre catch-alls: " + mark)
