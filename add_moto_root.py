# -*- coding: utf-8 -*-
# AGREGA CATCHER ADICIONAL DE MOTO COMO HIJO DEL CATCHER RAIZ (bot 61, #COMERCIAL).
# Solo responde a moto; cualquier otro mensaje hace {'next': True} y sigue al flujo
# existente (bot 62 valida cedula). NO se toca ningun bot existente.
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
        menu_key = "#COMERCIAL"
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
def build_code():
    code = BODY
    code = code.replace('__RESP_REQUISITOS__', json.dumps(resp_requisitos))
    code = code.replace('__RESP_CATALOGO__', json.dumps(resp_catalogo))
    code = code.replace('__RESP_SEGUIMIENTO__', json.dumps(resp_seguimiento))
    code = code.replace('__RESP_ENTREGA__', json.dumps(resp_entrega))
    code = code.replace('__RESP_UBICACION__', json.dumps(resp_ubicacion))
    return code

code = build_code()
try:
    compile(code, '<moto_root>', 'exec')
except SyntaxError as e:
    print('\u274c SYNTAX:', e); sys.exit(1)

# Verificar que bot 61 es #COMERCIAL y tiene hijos (es el catcher raiz)
r = call('acrux.chat.bot', 'read', [[61]], {'fields': ['id','name','bot_key','child_ids']})
if not r or not (r[0].get('child_ids')):
    print('\u274c bot 61 no existe o sin hijos:', r); sys.exit(1)
root_id = r[0]['id']
print(f"Catcher raiz #COMERCIAL = bot {root_id} ({r[0]['name']}) hijos={r[0]['child_ids']}")

# Reusar si ya existe (evita duplicados al reejecutar)
existing = call('acrux.chat.bot', 'search_read',
                [[('bot_key', '=', '#MOTO_CATCHER_61')]],
                {'fields': ['id', 'name', 'parent_id', 'sequence']})
if existing:
    new_id = existing[0]['id']
    call('acrux.chat.bot', 'write', [[new_id], {
        'parent_id': root_id, 'text_match': False, 'code': code, 'sequence': 1, 'active': True}])
    print(f"\u2705 Catcher moto ya existia: bot {new_id} (reutilizado/actualizado)")
else:
    new_id = call('acrux.chat.bot', 'create', [{
        'name': 'MOTO_CATCHER_COMERCIAL',
        'connector_id': 2,
        'parent_id': root_id,
        'text_match': False,
        'bot_key': '#MOTO_CATCHER_61',
        'code': code,
        'sequence': 1,
        'active': True,
    }])
    if not new_id:
        print('\u274c create fallo'); sys.exit(1)
    call('acrux.chat.bot', 'write', [[new_id], {'sequence': 1}])
    print(f"\u2705 Catcher moto creado: bot {new_id} (hijo de {root_id})")

# Verificar orden de hijos del catcher raiz
print('\n=== Hijos del catcher raiz (orden seq) ===')
kids = call('acrux.chat.bot', 'search_read', [[('parent_id', '=', root_id)]],
            {'fields': ['id','name','text_match','sequence','bot_key'], 'order': 'sequence'})
nomatch = [k for k in kids if not k.get('text_match')]
for k in kids:
    mark = '  <-- MOTO' if k['bot_key'] == '#MOTO_CATCHER_61' else ''
    print(f"  [{k['id']}] seq={k['sequence']} tm={str(k.get('text_match'))[:12]!r} {k['name']}{mark}")
moto_bot = next((k for k in nomatch if k['bot_key'] == '#MOTO_CATCHER_61'), None)
if moto_bot:
    before = all([k['id'] for k in nomatch].index(moto_bot['id']) < [k['id'] for k in nomatch].index(p) for p in [k['id'] for k in nomatch if k['bot_key'] != '#MOTO_CATCHER_61'])
    print('  => Moto catcher primero entre catch-alls del raiz:', '\u2705' if before else '\u274c')

# Simular enrutamiento a nivel raiz (thread = 61)
print('\n=== Simulacion a nivel raiz (children de 61) ===')
def simulate_root(raw):
    match = [k for k in kids if k.get('text_match')]
    nm = [k for k in kids if not k.get('text_match')]
    answer = match + nm
    lower = (raw or '').strip().lower()
    is_moto = ('moto' in lower) or ('motos' in lower) or ('creditomoto' in lower) or ('credito moto' in lower) or ('moto latinbien' in lower)
    sel = None
    for k in answer:
        if k.get('text_match') and k['text_match'] != raw:
            continue
        sel = k; break
    eff = sel
    if sel and sel['bot_key'] == '#MOTO_CATCHER_61' and not is_moto:
        idx = [k['id'] for k in nm].index(sel['id'])
        eff = [k for k in nm[idx+1:]][0] if [k for k in nm[idx+1:]] else None
    tag = 'MOTO' if (eff and eff['bot_key'] == '#MOTO_CATCHER_61') else ('FLUJO_EXISTENTE' if eff else 'NINGUNO')
    return sel['id'] if sel else None, (eff['id'] if eff else None, eff['name'] if eff else None), tag

for raw, desc in [('moto','palabra moto'),('recaudos para moto','requisitos'),('creditomoto','credito moto'),
                 ('donde quedan las motos','ubicacion'),('no tengo inicial para la moto','seguimiento'),
                 ('cuanto tardan las motos','entrega'),('12345678','cedula (flujo normal)'),
                 ('V12345678','cedula normal'),('hola','saludo normal'),('televisor','producto sin moto')]:
    sel, (eff_id, eff_name), tag = simulate_root(raw)
    print(f"  txt={raw!r:22} sel={sel} efectivo=[{eff_id}] {eff_name} -> {tag}  ({desc})")
