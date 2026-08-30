# -*- coding: utf-8 -*-
# FIX CONSULTA: los bots 102-105 deben volver al menu padre (goto_and_wait)
# para que el buscador tm=False capture el siguiente mensaje del usuario.
# Destinos con hijos: 65(#MENU_RECOMPRA), 66(#MENU_LC_APROBADA),
#                     64(#No tienes linea), 63(#Registro)
import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
API = 'https://latinbien.com/web/dataset/call_kw'

def call(model, method, args, kwargs=None):
    resp = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return resp.json().get('result')

targets = {
    102: "'#MENU_RECOMPRA'",     # RECOMPRA_CONSULTA -> menu 65 (hijo 106 tm=False busca)
    103: "'#MENU_LC_APROBADA'",  # LC_CONSULTA       -> menu 66 (hijo 107 tm=False busca)
    104: "'#No tienes linea'",   # REG_CONSULTA      -> menu 64 (hijo 108 tm=False busca)
    105: "'#Registro'",          # NR_CONSULTA       -> menu 63 (hijo 109 tm=False busca)
}
for bid, menu_key in targets.items():
    code = "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32\")', 'goto_and_wait': %s}]" % menu_key
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        print(f'❌ SYNTAX {bid}: {e}'); continue
    res = call('acrux.chat.bot', 'write', [[bid], {'code': code}])
    print(f'✅ Bot {bid}: goto_and_wait {menu_key} -> {res}')

# Verificar que los menus destino tienen hijos
menus = call('acrux.chat.bot', 'search_read', [[('id', 'in', [65, 66, 64, 63])]],
             {'fields': ['id', 'name', 'bot_key', 'child_ids']})
for m in menus:
    print(f"   Menu {m['id']} ({m['name']}) key={m.get('bot_key')} hijos={len(m.get('child_ids') or [])}")
