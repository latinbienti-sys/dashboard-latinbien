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

def read_bot(bot_id):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bot_id]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    return resp.json()['result'][0]

# First, read current VALIDAR_CEDULA code
current = read_bot(62)
current_code = current['code']
print('Current VALIDAR_CEDULA code length:', len(current_code))

# We need to rewrite VALIDAR_CEDULA to handle the "6" case INLINE
# When user types "6 <producto>", we search immediately
# When user types just "6", we tell them to use "6 <producto>"

# The new code will:
# 1. Check if texto starts with "6 " -> extract query, search products, show results + menu
# 2. Check if texto == "6" -> instruct user to write "6 <producto>"
# 3. Otherwise -> existing cedula validation logic (unchanged)

# We need to insert the "6" and "6 <producto>" handlers BEFORE the existing elif texto:

# Build the search code as a separate function to keep code clean
search_code = '''
# --- Search product function ---
def buscar_producto(query):
    Product = env['product.template']
    products = Product.search([('name', 'ilike', '%' + query + '%')], limit=3)
    if products:
        lines = ['Resultados para: ' + query + '\\\\n']
        for p in products:
            precio = p.list_price
            if precio and precio > 0:
                inicial = round(precio * 0.30, 2)
                cuota = round((precio - inicial) / 20, 2)
                lines.append(p.name)
                lines.append('Precio: $' + '{:.2f}'.format(precio))
                lines.append('Inicial (30%): $' + '{:.2f}'.format(inicial))
                lines.append('20 cuotas de: $' + '{:.2f}'.format(cuota))
                lines.append('')
            else:
                lines.append(p.name + ' - Consultar precio en tienda')
                lines.append('')
        lines.append('Catalogo: https://latinbien.com/shop/')
        return '\\\\n'.join(lines)
    else:
        return 'No encontre productos con "' + query + '".\\\\nIntenta con otras palabras o revisa nuestro catalogo:\\\\nhttps://latinbien.com/shop/'

'''

# Build the new full code
# We need to carefully merge: add "6" and "6 <producto>" handlers before cedula validation
new_code_lines = [
    '# === CODIGO DE VALIDAR CEDULA ===',
    '',
    'texto = (mess_id.text or "").strip()',
    '',
    '# --- Handler 1: Product search (6 <producto>) ---',
    'if texto.startswith("6 "):',
    '    query = texto[2:].strip()',
    '    if query:',
    '        result = buscar_producto(query)',
    '        menu = "\\\\n\\\\n1. Comprar a Credito\\\\n2. Comprar de Contado\\\\n3. Ver Catalogo\\\\n4. Convenio Corporativo\\\\n5. Reportar Problema\\\\n6. Consultar precio de un producto."',
    '        ret = [{"send_text": result + menu}]',
    '    else:',
    '        ret = [{"send_text": "Escribe el nombre del producto despues de 6, ej: 6 televisor"}]',
    '',
    '# --- Handler 2: Just "6" (ask for product name) ---',
    'elif texto == "6":',
    '    ret = [{"send_text": "Escribe el nombre del producto despues de 6, ej: 6 televisor"}]',
    '',
    '# --- Handler 3: Existing cedula validation ---',
    'elif texto:',
]

# Add the existing validation code after the "elif texto:" line
# The existing code follows after "elif texto:"
existing_after_elif = current_code.split('elif texto:', 1)[1]
# Keep everything after "elif texto:"
new_code_lines.append(existing_after_elif)

# Add the search function definition at the TOP of the code
# Actually we need to put the function before the if-elif chain

full_code = (
    'try:\n'
    + textwrap.indent(search_code.strip(), '    ') + '\n'
    + textwrap.indent('\n'.join(new_code_lines), '    ')
    + '\nexcept Exception as e:\n'
    + '    ret = [{"send_text": "Error: " + str(e)}]'
)

# Hmm this is getting complex. Let me use a different approach - just construct the full code directly.
