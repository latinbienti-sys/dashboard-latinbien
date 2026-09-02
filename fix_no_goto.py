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

# Update CONSULTA_PRECIO_6: send prompt ONLY, no goto_and_wait
menus = [(65, 'RECOMPRA'), (66, 'LC'), (64, 'REG'), (63, 'NR')]
for mid, mname in menus:
    resp = call(session, 'acrux.chat.bot', 'search_read',
        [[['parent_id', '=', mid], ['text_match', '=', '6']]],
        {'fields': ['id']}
    )
    kids = resp.get('result', [])
    if not kids:
        print('{}: no hijo 6'.format(mname))
        continue
    bid = kids[0]['id']
    code = "ret = [{'send_text': 'Escribe el nombre del producto que deseas consultar (ej: televisor 32 pulgadas)'}]"
    resp = call(session, 'acrux.chat.bot', 'write', [[bid], {'code': code}])
    ok = resp.get('result')
    print('{} hijo 6 (ID={}): {}'.format(mname, bid, 'OK' if ok else 'FAIL'))

# Show structure of MENU_RECOMPRA
print('\n--- MENU_RECOMPRA children ---')
resp = call(session, 'acrux.chat.bot', 'search_read',
    [[['parent_id', '=', 65]]],
    {'fields': ['id', 'name', 'text_match', 'sequence'], 'order': 'sequence asc'}
)
for b in resp.get('result', []):
    val = b['text_match']
    if val is False:
        tm = 'HANDLER'
    elif val:
        tm = "match={}".format(repr(val))
    else:
        tm = 'no match'
    seq = b['sequence']
    bid = b['id']
    name = b['name']
    print('  seq={} ID={} {} {}'.format(seq, bid, tm, name))

print('\n--- NEW FLOW ---')
print('1. Type "6" at menu -> you see the prompt (CONSULTA_PRECIO_6 sends text)')
print('2. Type product name -> BUSCAR_EN_RECOMPRA (handler seq=23) processes it')
print('3. Results shown, then returns to menu')
