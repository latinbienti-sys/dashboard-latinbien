import requests, json

session = requests.Session()
auth = {
    'jsonrpc': '2.0',
    'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
}
r = session.post('https://latinbien.com/web/session/authenticate', json=auth)
session.headers['Content-Type'] = 'application/json'

# Messages with literal \n for newlines in the Python code
updates = {
    68: "Excelente eleccion! Para procesar tu compra a credito, te transferire con un asesor especializado.\\n\\nPor favor espera un momento.",
    69: "Excelente! Puedes realizar tu compra de contado directamente en nuestro catalogo online.\\n\\nAccede ahora: https://latinbien.com/shop",
    67: "Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop",
    70: "Por favor, indicame de forma breve el inconveniente o duda que tengas.\\n\\nEscribe tu mensaje y te atenderemos.",
    72: "Excelente eleccion! Para procesar tu compra a credito, te transferire con un asesor especializado.\\n\\nPor favor espera un momento.",
    73: "Excelente! Puedes realizar tu compra de contado directamente en nuestro catalogo online.\\n\\nAccede ahora: https://latinbien.com/shop",
    71: "Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop",
    75: "Por favor, indicame de forma breve el inconveniente o duda que tengas.\\n\\nEscribe tu mensaje y te atenderemos.",
    92: "Excelente decision! Registra tus datos y solicita tu Linea de Credito:\\n\\nhttps://latinbien.com/registro",
    93: "Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop",
    94: "Compra de contado en nuestro catalogo online:\\n\\nhttps://latinbien.com/shop",
    96: "Por favor, indicame de forma breve el inconveniente o duda que tengas.\\n\\nEscribe tu mensaje y te atenderemos.",
    77: "Excelente decision! Registrate y solicita tu Linea de Credito:\\n\\nhttps://latinbien.com/registro",
    81: "Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop",
    82: "Compra de contado en nuestro catalogo online:\\n\\nhttps://latinbien.com/shop",
    83: "Por favor, indicame de forma breve el inconveniente o duda que tengas.\\n\\nEscribe tu mensaje y te atenderemos."
}

for bot_id, body_text in updates.items():
    # Use single quotes in the Python code, escape any single quotes in body
    safe_body = body_text.replace("'", "\\'")
    code = "ret = [{'send_text': '" + safe_body + "'}]"
    payload = {
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
            'model': 'acrux.chat.bot',
            'method': 'write',
            'args': [[bot_id], {'code': code}],
            'kwargs': {}
        }
    }
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json=payload)
    result = resp.json()
    if result.get('result') == True:
        print(f'Bot {bot_id}: OK')
    else:
        print(f'Bot {bot_id}: FAIL - {result}')
