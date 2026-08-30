import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Texto exacto que la usuaria pidio para "Reportar problema"
TEXTO_PROBLEMA = (
    "Por favor, indicame de forma breve en un solo mensaje:\n"
    "Si el inconveniente que estas presentando o la duda es sobre tus cuotas quincenales.\n"
    "Si se trata de un error en la plataforma.\n\n"
    "Escribe tu mensaje y te atenderemos a la brevedad."
)

# Bots de "Reportar problema" y su menu destino
BOTS_PROBLEMA = [
    (70, '#MENU_RECOMPRA'),     # RECOMPRA_PROBLEMA
    (75, '#MENU_LC_APROBADA'),  # LC_PROBLEMA
    (96, '#No tienes linea'),   # REG_PROBLEMA
    (83, '#Registro'),          # NR_PROBLEMA
]

for bot_id, goto_key in BOTS_PROBLEMA:
    # Codigo: separar send_text y goto_and_wait como acciones independientes
    code = (
        "ret = ["
        "{'send_text': '''" + TEXTO_PROBLEMA + "'''}, "
        "{'goto_and_wait': '" + goto_key + "'}"
        "]"
    )
    
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {
            'model': 'acrux.chat.bot',
            'method': 'write',
            'args': [[bot_id], {
                'code': code,
                'body_whatsapp': False
            }],
            'kwargs': {}
        }
    })
    result = resp.json()
    if result.get('result') == True:
        print(f'Bot {bot_id} OK')
    else:
        print(f'Bot {bot_id} ERROR: {result.get("error", {}).get("message", "???")}')

# Verificar lo que quedo
print('\n--- Verificacion ---')
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['id', 'in', [70, 75, 96, 83]]]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
for b in resp.json().get('result', []):
    print(f'\n{b["id"]} {b["name"]}:')
    print(f'  {b["code"]}')
