# -*- coding: utf-8 -*-
# VERIFICACION: (a) leer codigo almacenado de los 4 bots nuevos,
# (b) simular el algoritmo real de enrutamiento de Bot.py para varios mensajes.
import requests, sys
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

MOTO_BOTS = {126: '#MENU_RECOMPRA', 127: '#MENU_LC_APROBADA', 128: '#No tienes linea', 129: '#Registro'}

print('=== (a) Codigo almacenado (primeras 700 chars de cada bot nuevo) ===')
for bid in MOTO_BOTS:
    b = call('acrux.chat.bot', 'read', [[bid]], {'fields': ['id','name','code','sequence','text_match','bot_key']})[0]
    print(f"\n--- Bot {bid} {b['name']} (seq={b['sequence']}, tm={b['text_match']!r}, key={b['bot_key']!r}) ---")
    print(b['code'][:700])

print('\n\n=== (b) Simulacion de enrutamiento (igual que Bot.py _bot_get) ===')
def simulate(menu_id, raw_text):
    # Cargar hijos del menu en orden seq (match + no_match)
    kids = call('acrux.chat.bot', 'search_read', [[('parent_id', '=', menu_id)]],
                {'fields': ['id','name','text_match','sequence','bot_key'], 'order': 'sequence'})
    match = [k for k in kids if k.get('text_match')]
    nomatch = [k for k in kids if not k.get('text_match')]
    answer_ids = match + nomatch  # orden real de Bot.py
    lower = (raw_text or '').strip().lower()
    is_moto = ('moto' in lower) or ('motos' in lower) or ('creditomoto' in lower) or ('credito moto' in lower) or ('moto latinbien' in lower)
    # primer bot seleccionado por text_match exacto
    selected = None
    for k in answer_ids:
        tm = k.get('text_match')
        if tm and tm != raw_text:
            continue
        selected = k
        break
    sel_id = selected['id'] if selected else None
    # Si el seleccionado es el bot moto y NO hay keyword moto -> next -> siguiente no_match (buscador de precio)
    efectivo = selected
    if sel_id in MOTO_BOTS and not is_moto:
        idx = [k['id'] for k in nomatch].index(sel_id)
        rest = [k for k in nomatch[idx+1:]]
        efectivo = rest[0] if rest else None
    return sel_id, (efectivo['id'] if efectivo else None, efectivo['name'] if efectivo else None), is_moto

tests = [
    ('1', 'opcion de menu 1'),
    ('6', 'opcion de menu 6 (consulta precio)'),
    ('moto', 'palabra clave moto'),
    ('recaudos para mi moto', 'requisitos moto'),
    ('creditomoto', 'credito moto'),
    ('donde quedan las motos', 'ubicacion moto'),
    ('no tengo inicial para la moto', 'seguimiento sin inicial'),
    ('cuanto tardan las motos', 'tiempo de entrega'),
    ('televisor 32 pulgadas', 'producto SIN moto (debe ir al buscador)'),
    ('nevera', 'producto SIN moto (debe ir al buscador)'),
    ('credito', 'credito solo, sin moto (NO debe capturar campana)'),
]
for menu_id in [65, 66, 64, 63]:
    mname = {65:'RECOMPRA',66:'LC_APROBADA',64:'REGISTRADO',63:'NO_REGISTRADO'}[menu_id]
    print(f"\n### MENU {menu_id} ({mname}) ###")
    for raw, desc in tests:
        sel, (eff_id, eff_name), is_moto = simulate(menu_id, raw)
        tag = 'MOTO' if (eff_id in MOTO_BOTS) else ('PRECIO/OTRO' if eff_id else 'NINGUNO')
        print(f"  txt={raw!r:35} sel={sel} efectivo=[{eff_id}] {eff_name}  -> {tag}  ({desc})")
