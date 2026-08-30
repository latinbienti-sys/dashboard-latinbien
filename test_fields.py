import requests, json

session = requests.Session()
r = session.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
session.headers['Content-Type'] = 'application/json'

# Check fields of acrux.chat.message
resp = session.post('https://latinbien.com/web/dataset/call_kw/ir.model.fields/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model.fields', 'method': 'search_read',
        'args': [[['model_id.model', '=', 'acrux.chat.message'], ['name', 'in', ['conversation_id', 'contact_id', 'text']]]],
        'kwargs': {'fields': ['name', 'field_description', 'ttype', 'relation']}
    }
})
print('Fields of acrux.chat.message:')
for f in resp.json().get('result', []):
    print(f"  {f['name']} ({f.get('field_description','?')}) type={f.get('ttype','?')} relation={f.get('relation','?')}")

# Check fields of acrux.chat.conversation - specifically note
resp = session.post('https://latinbien.com/web/dataset/call_kw/ir.model.fields/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model.fields', 'method': 'search_read',
        'args': [[['model_id.model', '=', 'acrux.chat.conversation'], ['name', 'in', ['note', 'bot_id', 'partner_id']]]],
        'kwargs': {'fields': ['name', 'field_description', 'ttype', 'relation']}
    }
})
print('\nFields of acrux.chat.conversation:')
for f in resp.json().get('result', []):
    print(f"  {f['name']} ({f.get('field_description','?')}) type={f.get('ttype','?')} relation={f.get('relation','?')}")
