from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Try call_kw for connector
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.connector','method':'search_read',
        'args':[[('id','=',2)]],
        'kwargs':{'fields':['id','name','start_message','bot_id','type'], 'limit':10}
    }
})
print("Connector 2:")
data = resp.json()
if 'result' in data and data['result']:
    for c in data['result']:
        print(json.dumps(c, indent=2, default=str)[:1000])
else:
    print("No result:", str(data)[:500])

# Try to find start_message field
print("\n\nAll fields of acrux.chat.connector:")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/fields_get', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.connector','method':'fields_get',
        'args':[[]],'kwargs':{'attributes':['string','type','relation']}
    }
})
fields = resp.json().get('result', {})
for fname, finfo in sorted(fields.items()):
    if 'start' in fname.lower() or 'welcome' in fname.lower() or 'message' in fname.lower() or 'bot' in fname.lower():
        print(f"  {fname}: {finfo.get('string','?')} type={finfo.get('type','?')}")
