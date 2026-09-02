import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def call(session, model, method, args=None, kwargs=None):
    if kwargs is None:
        kwargs = {}
    resp = session.post('https://latinbien.com/web/dataset/call_kw/' + model + '/' + method, json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs}
    })
    return resp.json()

# Create BUSCADOR under each menu
menus_config = [
    (65, 'MENU_RECOMPRA', 'BUSCAR_EN_RECOMPRA', '#MENU_RECOMPRA'),
    (66, 'MENU_LC_APROBADA', 'BUSCAR_EN_LC', '#MENU_LC_APROBADA'),
    (64, 'MENU_REGISTRADO', 'BUSCAR_EN_REG', '#MENU_REGISTRADO'),
    (63, 'MENU_NO_REGISTRADO', 'BUSCAR_EN_NR', '#MENU_NO_REGISTRADO'),
]

for menu_id, menu_name, bot_name, return_target in menus_config:
    # Create search handler under this menu
    search_code = (
        "\n"
        "try:\n"
        "    query = mess_id.text.strip()\n"
        "    Product = env['product.template']\n"
        "    products = Product.search([('name', 'ilike', '%' + query + '%')], limit=3)\n"
        "    if products:\n"
        "        lines = ['Resultados para: ' + query + '\\n']\n"
        "        for p in products:\n"
        "            precio = p.list_price\n"
        "            if precio and precio > 0:\n"
        "                inicial = round(precio * 0.30, 2)\n"
        "                cuota = round((precio - inicial) / 20, 2)\n"
        "                lines.append(p.name)\n"
        "                lines.append('Precio: $' + '{:.2f}'.format(precio))\n"
        "                lines.append('Inicial (30%): $' + '{:.2f}'.format(inicial))\n"
        "                lines.append('20 cuotas de: $' + '{:.2f}'.format(cuota))\n"
        "                lines.append('')\n"
        "            else:\n"
        "                lines.append(p.name + ' - Consultar precio en tienda')\n"
        "                lines.append('')\n"
        "        lines.append('Catalogo: https://latinbien.com/shop/')\n"
        "        msg = '\\n'.join(lines)\n"
        "    else:\n"
        "        msg = 'No encontre productos con \"' + query + '\".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/'\n"
        "except Exception as e:\n"
        "    msg = 'Error al buscar: ' + str(e)\n"
        "\n"
        "ret = [{'send_text': msg, 'goto_and_wait': '" + return_target + "'}]\n"
    )
    
    resp = call(session, 'acrux.chat.bot', 'create', [{
        'name': bot_name,
        'parent_id': menu_id,
        'text_match': False,  # handler
        'sequence': 50,
        'code': search_code,
        'body_whatsapp': False,
        'active': True,
    }])
    new_id = resp.get('result')
    if new_id:
        print(f'{menu_name}: BUSCADOR creado (ID={new_id})')
    else:
        print(f'{menu_name}: ERROR - {resp.get("error",{}).get("message","?")}')
        continue
    
    # Update the CONSULTA_PRECIO_6 child to navigate to THIS BUSCADOR
    resp2 = call(session, 'acrux.chat.bot', 'search_read',
        [[['parent_id', '=', menu_id], ['text_match', '=', '6']]],
        {'fields': ['id']}
    )
    kids6 = resp2.get('result', [])
    if kids6:
        child6_id = kids6[0]['id']
        # Code: send_text then goto_and_wait to the new BUSCADOR
        child_code = (
            "ret = [\n"
            "    {'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32 pulgadas)'},\n"
            "    {'goto_and_wait': '#" + bot_name + "'}\n"
            "]"
        )
        resp3 = call(session, 'acrux.chat.bot', 'write', [[child6_id], {'code': child_code}])
        if resp3.get('result'):
            print(f'  -> Hijo "6" actualizado para navegar a {bot_name}')
        else:
            print(f'  -> Error actualizando hijo "6": {resp3.get("error",{}).get("message","?")}')
    else:
        print(f'  -> No se encontro hijo "6" en {menu_name}')

print('\n--- LISTO ---')
print('Ahora cada menu tiene su propio BUSCADOR')
print('El hijo "6" navega al BUSCADOR del mismo menu')
