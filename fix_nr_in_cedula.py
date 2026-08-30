import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Read current code
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
code = resp.json()['result'][0]['code']

# Add NR menu handlers BEFORE the cedula validation
# The current structure is:
# if texto == '6': instruction
# elif texto: cedula validation
#
# New structure:
# if texto.startswith('6 '): product search
# elif texto == '6': instruction
# elif texto in ('1','2','3','4','5'): NR menu options
# elif texto: cedula validation

# Find the insertion point - right after 'if texto == "6":' block and before 'elif texto:'
# We need to add the NR handler between them

old = ("if texto == '6':\n"
       "    ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 televisor'}]\n"
       "elif texto:")

new = ("if texto == '6':\n"
       "    ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 televisor'}]\n"
       "elif texto == '1':\n"
       "    ret = [{'send_text': 'Excelente decision! Registrate y solicita tu Linea de Credito:\\n\\nhttps://latinbien.com/registro'}]\n"
       "elif texto == '2':\n"
       "    ret = [{'send_text': 'Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop'}]\n"
       "elif texto == '3':\n"
       "    ret = [{'send_text': 'Compra de contado en nuestro catalogo online:\\n\\nhttps://latinbien.com/shop'}]\n"
       "elif texto == '4':\n"
       "    ret = [{'send_text': 'Perfecto! He recopilado toda tu informacion con exito. Para garantizarte una asesoria completamente personalizada, te estoy transfiriendo en este instante con uno de nuestros asesores.'}, {'clear_catcher': True}]\n"
       "elif texto == '5':\n"
       "    ret = [{'send_text': 'Perfecto! He recopilado toda tu informacion con exito. Para garantizarte una asesoria completamente personalizada, te estoy transfiriendo en este instante con uno de nuestros asesores.'}, {'clear_catcher': True}]\n"
       "elif texto:")

if old in code:
    new_code = code.replace(old, new, 1)
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - VALIDAR_CEDULA updated with NR menu handlers')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print('Old block not found!')
    # Show what we have around 'if texto'
    idx = code.find('if texto')
    print('Current:', repr(code[idx:idx+200]))
