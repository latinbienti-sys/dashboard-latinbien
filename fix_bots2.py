import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# For each sub-bot: code returns send_text AND goto_and_wait back to parent menu
# So the user stays at the menu level and can keep selecting options

updates = {
    # Under MENU_RECOMPRA (65) - bot_key: #MENU_RECOMPRA
    68: ("#MENU_RECOMPRA", "Excelente eleccion! Para procesar tu compra a credito, te transferire con un asesor especializado.\\n\\nPor favor espera un momento."),
    69: ("#MENU_RECOMPRA", "Excelente! Puedes realizar tu compra de contado directamente en nuestro catalogo online.\\n\\nAccede ahora: https://latinbien.com/shop"),
    67: ("#MENU_RECOMPRA", "Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop"),
    70: ("#MENU_RECOMPRA", "Por favor, indicame de forma breve el inconveniente o duda que tengas.\\n\\nEscribe tu mensaje y te atenderemos."),
    # Under MENU_LC_APROBADA (66) - bot_key: #MENU_LC_APROBADA
    72: ("#MENU_LC_APROBADA", "Excelente eleccion! Para procesar tu compra a credito, te transferire con un asesor especializado.\\n\\nPor favor espera un momento."),
    73: ("#MENU_LC_APROBADA", "Excelente! Puedes realizar tu compra de contado directamente en nuestro catalogo online.\\n\\nAccede ahora: https://latinbien.com/shop"),
    71: ("#MENU_LC_APROBADA", "Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop"),
    75: ("#MENU_LC_APROBADA", "Por favor, indicame de forma breve el inconveniente o duda que tengas.\\n\\nEscribe tu mensaje y te atenderemos."),
    # Under MENU_REGISTRADO (64) - bot_key: #No tienes linea
    92: ("#No tienes linea", "Excelente decision! Registra tus datos y solicita tu Linea de Credito:\\n\\nhttps://latinbien.com/registro"),
    93: ("#No tienes linea", "Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop"),
    94: ("#No tienes linea", "Compra de contado en nuestro catalogo online:\\n\\nhttps://latinbien.com/shop"),
    96: ("#No tienes linea", "Por favor, indicame de forma breve el inconveniente o duda que tengas.\\n\\nEscribe tu mensaje y te atenderemos."),
    # Under MENU_NO_REGISTRADO (63) - bot_key: #Registro
    77: ("#Registro", "Excelente decision! Registrate y solicita tu Linea de Credito:\\n\\nhttps://latinbien.com/registro"),
    81: ("#Registro", "Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop"),
    82: ("#Registro", "Compra de contado en nuestro catalogo online:\\n\\nhttps://latinbien.com/shop"),
    83: ("#Registro", "Por favor, indicame de forma breve el inconveniente o duda que tengas.\\n\\nEscribe tu mensaje y te atenderemos.")
}

for bot_id, (menu_key, body_text) in updates.items():
    # Build code with goto_and_wait to keep user at menu level
    safe_body = body_text.replace("'", "\\'")
    code = "ret = [{'send_text': '" + safe_body + "', 'goto_and_wait': '" + menu_key + "'}]"
    
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {
            'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bot_id], {'code': code}], 'kwargs': {}
        }
    })
    result = resp.json()
    if result.get('result') == True:
        print(f'Bot {bot_id}: OK -> goto_and_wait: {menu_key}')
    else:
        print(f'Bot {bot_id}: FAIL - {result}')
