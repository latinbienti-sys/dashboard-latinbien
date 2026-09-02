from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Get ALL fields of acrux.chat.bot
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/fields_get', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'fields_get',
        'args':[[]],'kwargs':{'attributes':['string','type','relation']}
    }
})
fields = resp.json().get('result', {})
if not fields:
    print("Error getting fields:", str(resp.json())[:500])
else:
    print("Fields of acrux.chat.bot:")
    for fname, finfo in sorted(fields.items()):
        print(f"  {fname}: {finfo.get('string','?')} ({finfo.get('type','?')}) rel={finfo.get('relation','')}")
