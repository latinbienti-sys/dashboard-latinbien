from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Try to read a conversation directly
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.conversation', 'method': 'read',
        'args': [[30719, 30729, 31931]],
        'kwargs': {'fields': ['id', 'name', 'active_bot_id', 'is_bot_active']}
    }
})
r = resp.json()
if 'result' in r:
    for conv in r['result']:
        print(f'Conversation {conv["id"]}: {conv.get("name")}')
        print(f'  active_bot_id: {conv.get("active_bot_id")}')
        print(f'  is_bot_active: {conv.get("is_bot_active")}')
else:
    print('Error reading conversations:', r.get('error', {}).get('message', 'unknown')[:200])

print()

# If I can't read conversations, let me try to write (clear active_bot)
# First, let's see if there's a method to reset
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/ir.model/search', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'ir.model', 'method': 'search',
        'args': [],
        'kwargs': {'domain': [['model', '=', 'acrux.chat.conversation']]}
    }
})
if resp2.json().get('result'):
    print('Conversation model exists')
    # Try fields_get
    resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/fields_get', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.conversation', 'method': 'fields_get',
            'args': [],
            'kwargs': {'attributes': ['string', 'type']}
        }
    })
    fields = resp3.json().get('result', {})
    print('Conversation fields with active_bot:')
    for fname, finfo in sorted(fields.items()):
        if 'active' in fname.lower() or 'bot' in fname.lower():
            print(f'  {fname}: {finfo.get("string")} ({finfo.get("type")})')
