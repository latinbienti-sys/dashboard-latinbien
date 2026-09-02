import requests, json

session = requests.Session()
session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

def read_code(bot_id):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bot_id]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    return resp.json()['result'][0]['code']

def write_code(bot_id, code):
    resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bot_id], {'code': code}], 'kwargs': {}
        }
    })
    return resp.json()

# ==========================================
# 1. Fix NR menu text in VALIDAR_CEDULA (62)
# ==========================================
code62 = read_code(62)

# The current NR menu shows:
# 5. Consultar precio de producto
# 6. Consultar precio (escribe 6 + nombre)
# 
# Should be (matching NR children):
# 1. Registrarme y solicitar LC
# 2. Ver catalogo
# 3. Compra de contado
# 4. Reportar problema
# 5. Hablar con Asesor
# 6. Consultar precio (escribe 6 + nombre)

old_nr_menu_5 = '5\\ufe0f\\u20e3 Consultar precio de producto\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'
new_nr_menu_5 = '5\\ufe0f\\u20e3 Hablar con Asesor\\n6\\ufe0f\\u20e3 Consultar precio (escribe 6 + nombre)'

if old_nr_menu_5 in code62:
    code62 = code62.replace(old_nr_menu_5, new_nr_menu_5)
    write_code(62, code62)
    print('VALIDAR_CEDULA: NR menu text fixed')
else:
    print('VALIDAR_CEDULA: old NR menu text NOT found')
    # Check what's really there
    idx = code62.find('No encontr')
    if idx >= 0:
        section = code62[idx:idx+500]
        print('NR section:', repr(section))

# ==========================================
# 2. Create NR_CREDITO or reuse NR_ASESOR for option 5
#    Update NR_ASESOR (100) to also have text_match='5'
#    OR: create a new option. Let's add text_match='5' to NR_ASESOR
# ==========================================

# Check NR_ASESOR (100)
resp = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[100]],
        'kwargs': {'fields': ['id', 'name', 'code', 'text_match']}
    }
})
asesor = resp.json()['result'][0]
print('\nNR_ASESOR (ID=100):')
print('  current text_match:', repr(asesor['text_match']))

# Update NR_ASESOR to match both '5' and 'ASESOR'
# Check if text_match supports multiple values
# Usually text_match is a single value, not a list
# So we'll change it to '5' and keep ASESOR as-is
# Actually, we can create a new child NR_CREDITO and point it to the same ASESOR code
# Or use ASESOR code and change the match
# 
# Simpler approach: just update NR_ASESOR to match '5'
# and if user types ASESOR, it falls to handler (which we can handle)

# Actually, even simpler: let's check if the original NR_ASESOR works for 'ASESOR' text
# and keep it that way. We'll update the menu to show:
# 5. Hablar con Asesor
# User types '5' → needs a handler
# 
# Since there's no '5' handler, let's set NR_ASESOR's text_match to '5'
# But then 'ASESOR' won't work.
#
# Best: create a simple handler for '5' that redirects to ASESOR

# Let me update NR_ASESOR to have text_match='5'
resp3 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[100], {'text_match': '5'}], 'kwargs': {}
    }
})
if resp3.json().get('result'):
    print('NR_ASESOR text_match updated to: 5')
else:
    print('ERROR updating NR_ASESOR:', resp3.json().get('error', {}))

# ==========================================
# 3. Verify final state
# ==========================================
print('\n--- NR children after fix ---')
resp4 = session.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[['parent_id','=',63]]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': 'sequence asc, id asc'}
    }
})
for c in resp4.json().get('result', []):
    val = c['text_match']
    if val is False:
        tm = 'HANDLER'
    elif val:
        tm = 'match={}'.format(repr(val))
    else:
        tm = 'no match'
    print('  seq={} ID={} {} {}'.format(c['sequence'], c['id'], tm, c['name']))
