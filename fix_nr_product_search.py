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

# Find where to insert: after elif texto == '5': block, before elif texto:
import re

# Find elif texto == '5': block
idx5 = code.find("elif texto == '5':")
# Find the subsequent elif texto:
idx_elif = code.find("\nelif texto:", idx5)

if idx5 >= 0 and idx_elif > idx5:
    # Extract the '5' handler text
    five_block = code[idx5:idx_elif]
    print("Found '5' block:")
    print(five_block[:200])
    
    # New handler for '6 <query>'
    new_handler = '''
elif len(texto) > 2 and texto[0:1] == '6' and texto[1:2] == ' ':
    query = texto[2:].strip()
    if query:
        Product = env['product.template']
        products = Product.search([('website_published', '=', True), ('name', 'ilike', '%' + query + '%')], limit=5)
        if products:
            lines = ['Resultados para: ' + query + '\\n']
            for p in products:
                precio = p.list_price
                if precio and precio > 1.0:
                    inicial = round(precio * 0.30, 2)
                    cuota = round((precio - inicial) / 20, 2)
                    lines.append(p.name)
                    lines.append('Precio: $' + '{:,.2f}'.format(precio))
                    lines.append('Inicial (30%): $' + '{:,.2f}'.format(inicial))
                    lines.append('20 cuotas de: $' + '{:,.2f}'.format(cuota))
                    lines.append('')
            if len(lines) > 1:
                lines.append('Catalogo: https://latinbien.com/shop/')
                msg = '\\n'.join(lines)
            else:
                msg = 'No tenemos "' + query + '" disponible en este momento, pero podemos cotizarlo para ti.\\nEscribe COTIZAR y un asesor te contactara.'
        else:
            msg = 'No tenemos "' + query + '" disponible en este momento, pero podemos cotizarlo para ti.\\nEscribe COTIZAR y un asesor te contactara.'
        menu = '\\n\\n1. Registrarme y solicitar LC\\n2. Ver catalogo\\n3. Compra de contado\\n4. Reportar problema\\n5. Hablar con Asesor\\n6. Consultar precio (escribe 6 + nombre)'
        ret = [{'send_text': msg + menu}]
    else:
        ret = [{'send_text': 'Escribe 6 seguido del nombre del producto, ej: 6 nevera'}]
    
'''
    
    new_code = code[:idx_elif] + new_handler + code[idx_elif:]
    
    # Verify
    lines_before = len(code.split('\n'))
    lines_after = len(new_code.split('\n'))
    print(f"\nLines: {lines_before} -> {lines_after}")
    
    # Check it's valid Python syntax by compiling
    try:
        compile(new_code, '<string>', 'exec')
        print("Syntax check: OK")
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        # Show the problem area
        lines = new_code.split('\n')
        print(f"Around line {e.lineno}:")
        for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
            print(f"  {i+1}: {lines[i]}")
        exit()
    
    # Write
    resp2 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': new_code}], 'kwargs': {}
        }
    })
    if resp2.json().get('result'):
        print('OK - Product search handler added for NR users')
    else:
        print('ERROR:', resp2.json().get('error', {}))
else:
    print(f"Could not find: idx5={idx5}, idx_elif={idx_elif}")
    # Debug: show relevant part
    print("\nCode around the area:")
    print(code[400:600])
