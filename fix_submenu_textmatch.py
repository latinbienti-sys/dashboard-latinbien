import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

def write_bot(bid, data):
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[bid], data], 'kwargs': {}
        }
    })
    return resp.json().get('result', False)

# Give unique text_match to sub-menu children of bot 62
changes = {
    65: {'text_match': '__MENU_RECOMPRA__'},
    66: {'text_match': '__MENU_LC_APROBADA__'},
    64: {'text_match': '__MENU_REGISTRADO__'},
    63: {'text_match': '__MENU_NO_REGISTRADO__'},
}

for bid, data in changes.items():
    if write_bot(bid, data):
        print(f"✅ Bot {bid}: text_match = {data['text_match']}")
    else:
        print(f"❌ Bot {bid}: error")

print("\nListo. Ahora los sub-menús ya no interceptarán mensajes generales.")
print("Prueba enviando 'hola' y luego 'v15921224' al número comercial.")
