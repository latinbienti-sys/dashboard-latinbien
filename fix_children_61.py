import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
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

# Fix bot 84: set text_match to a keyword so it only triggers on explicit command
if write_bot(84, {'text_match': '__TRANSFERIR__'}):
    print("✅ Bot 84: text_match = '__TRANSFERIR__' (no interfiere con mensajes normales)")
else:
    print("❌ Bot 84 error")

# Fix bot 101 (BUSCAR_PRODUCTO): also has no text_match
# Set it to trigger on specific text
if write_bot(101, {'text_match': '__BUSCAR__'}):
    print("✅ Bot 101: text_match = '__BUSCAR__'")
else:
    print("❌ Bot 101 error")

# Verify children now
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[('parent_id', '=', 61)]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'sequence']}
    }
})
print(f"\nChildren of bot 61:")
for b in resp.json().get('result', []):
    tm = str(b.get('text_match','') or '(empty)')[:25]
    seq = str(b.get('sequence','') or '0')
    print(f"  Bot {b['id']:>3}: {b['name'][:45]:<45} text_match={tm:<25} seq={seq}")
