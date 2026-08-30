# -*- coding: utf-8 -*-
# FIX IMAGENES/PDF -> PRECIOS (conector 2 comercial)
# Los bots de busqueda/precio con text_match=False capturan CUALQUIER mensaje,
# incluyendo imagenes/PDF/audio (ttype != 'text') con text vacio, y devuelven
# "Resultados para:" con precios.
#
# Solucion: al inicio de cada bot, si el mensaje NO es texto (o texto vacio),
# responder mensaje amable y mantener el menu (goto_and_wait al menu padre).
import requests, json, sys, textwrap
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

def get_code(bid):
    bots = call('acrux.chat.bot', 'search_read', [[('id', '=', bid)]], {'fields': ['id', 'code']})
    return bots and bots[0].get('code') or ''

def safe_write(bid, name, code):
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        print(f'❌ SYNTAX {name} ({bid}): {e}')
        return
    res = call('acrux.chat.bot', 'write', [[bid], {'code': code}])
    print(f'✅ Bot {bid} ({name}): {res}')

# Mensaje amable para imagen/PDF/audio/texto vacio
MSG_GUARD = ('📎 *No puedo procesar imágenes ni documentos* para consultar precios.\n\n'
             'Por favor escribe el *nombre del producto* para ver su precio.\n\n'
             'Ejemplo: *6 civic*')

# menu destino por bot (el mismo que ya usan en su ret final)
TARGETS = {
    106: '#MENU_RECOMPRA',      # RECOMPRA_BUSCAR (padre 65)
    107: '#MENU_LC_APROBADA',   # LC_BUSCAR (padre 66)
    108: '#No tienes linea',    # REG_BUSCAR (padre 64)
    109: '#Registro',           # NR_BUSCAR (padre 63)
    117: '#COMERCIAL',          # PROCESAR_BUSQUEDA (padre 101)
    122: '#MENU_RECOMPRA',      # BUSCAR_EN_RECOMPRA (padre 65)
    123: '#MENU_LC_APROBADA',   # BUSCAR_EN_LC (padre 66)
    124: '#No tienes linea',    # BUSCAR_EN_REG (padre 64)
    125: '#Registro',           # BUSCAR_EN_NR (padre 63)
}

GUARD_HEADER = ("if mess_id.ttype != 'text' or not (mess_id.text or '').strip():\n"
                "    ret = [{'send_text': " + repr(MSG_GUARD) + ", 'goto_and_wait': " + "'%s'})\n"
                "else:\n")

for bid, menu_key in TARGETS.items():
    name_info = call('acrux.chat.bot', 'read', [[bid]], {'fields': ['name']})[0]['name']
    code = get_code(bid)
    if not code.strip():
        print(f'⚠️ Bot {bid} sin code, se omite')
        continue
    # Reemplazar el menu key en el header de guarda
    guard = ("if mess_id.ttype != 'text' or not (mess_id.text or '').strip():\n"
             "    ret = [{'send_text': " + repr(MSG_GUARD) + ", 'goto_and_wait': '" + menu_key + "'}]\n"
             "else:\n")
    new_code = guard + textwrap.indent(code, '    ')
    safe_write(bid, name_info, new_code)

# ============ VERIFICAR ============
print('\n=== VERIFICACION ===')
for bid in TARGETS:
    bots = call('acrux.chat.bot', 'search_read', [[('id', '=', bid)]], {'fields': ['id', 'name', 'code']})
    c = bots[0]['code'] or ''
    ok = ("mess_id.ttype != 'text'" in c) and ('goto_and_wait' in c)
    print(f"  Bot {bid} ({bots[0]['name'][:40]}): {'✅ guarda OK' if ok else '❌ FALTA GUARDA'}")
