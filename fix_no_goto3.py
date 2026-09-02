import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def write_bot(bot_id, code):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bot_id], {'code': code}], 'kwargs': {}}
    })
    return resp.json()

MENU_TEXTS = {
    'RECOMPRA': '1. Comprar a Credito\n2. Comprar de Contado\n3. Ver Catalogo\n4. Convenio Corporativo\n5. Reportar Problema\n6. Consultar precio de un producto.',
    'LC':       '1. Comprar a Credito\n2. Comprar de Contado\n3. Ver Catalogo\n4. Convenio Corporativo\n5. Reportar Problema\n6. Consultar precio de un producto.',
    'REG':      '1. Comprar a Credito\n2. Comprar de Contado\n3. Ver Catalogo\n4. Convenio Corporativo\n5. Reportar Problema\n6. Consultar precio de un producto.',
    'NR':       '1. Registrarme (llenar formulario)\n2. Ver Catalogo\n3. Hablar con Asesor\n4. Reportar Problema\n5. Comprar a Credito\n6. Consultar precio de un producto.',
}

BOTS = {
    'BUSCAR_EN_RECOMPRA': 122,
    'BUSCAR_EN_LC':       123,
    'BUSCAR_EN_REG':      124,
    'BUSCAR_EN_NR':       125,
}

for name, bid in BOTS.items():
    suffix = name.split('_')[-1]
    menu_text = MENU_TEXTS[suffix]
    # Escape newlines in menu text so they become \n in the code
    menu_text_escaped = menu_text.replace('\n', '\\n')
    
    # Build the else branch text parts
    else_part1 = 'No encontre productos con "'
    else_part2 = '".\\nIntenta con otras palabras o revisa nuestro catalogo:\\nhttps://latinbien.com/shop/'
    
    lines = []
    lines.append('try:')
    lines.append('    query = mess_id.text.strip()')
    lines.append("    Product = env['product.template']")
    lines.append("    products = Product.search([('name', 'ilike', '%' + query + '%')], limit=3)")
    lines.append('    if products:')
    lines.append("        lines = ['Resultados para: ' + query + '\\n']")
    lines.append('        for p in products:')
    lines.append('            precio = p.list_price')
    lines.append('            if precio and precio > 0:')
    lines.append('                inicial = round(precio * 0.30, 2)')
    lines.append('                cuota = round((precio - inicial) / 20, 2)')
    lines.append('                lines.append(p.name)')
    lines.append("                lines.append('Precio: $' + '{:.2f}'.format(precio))")
    lines.append("                lines.append('Inicial (30%): $' + '{:.2f}'.format(inicial))")
    lines.append("                lines.append('20 cuotas de: $' + '{:.2f}'.format(cuota))")
    lines.append("                lines.append('')")
    lines.append('            else:')
    lines.append("                lines.append(p.name + ' - Consultar precio en tienda')")
    lines.append("                lines.append('')")
    lines.append("        lines.append('Catalogo: https://latinbien.com/shop/')")
    lines.append("        msg = '\\n'.join(lines)")
    lines.append('    else:')
    # Build: msg = 'No encontre productos con "' + query + '".\nIntenta...\nhttps://...'
    lines.append("        msg = '" + else_part1 + "' + query + '" + else_part2 + "'")
    lines.append('except Exception as e:')
    lines.append('    msg = "Error al buscar: " + str(e)')
    lines.append('')
    # ret line with escaped menu text
    lines.append("ret = [{'send_text': msg + '\\n\\n" + menu_text_escaped + "'}]")
    
    full_code = '\n'.join(lines)
    
    resp = write_bot(bid, full_code)
    ok = resp.get('result')
    if ok:
        print('{} (ID={}): OK'.format(name, bid))
    else:
        err = resp.get('error', {})
        print('{} (ID={}): FAIL - {}'.format(name, bid, err.get('data', {}).get('message', str(err))))
    
    # Print generated code for first bot for verification
    if bid == 122:
        print('\n--- Generated Code (ID=122) ---')
        print(full_code)
        print('---')
