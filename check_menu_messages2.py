from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

print("Session OK")

# Try reading bots with call_kw
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'search_read',
        'args':[[('id','in',[61,62,65,66,64,63])]],
        'kwargs':{'fields':['id','name','message','text_match','sequence','parent_id'],
            'limit':10}
    }
})
print(f"\nsearch_read result type: {type(resp.json().get('result'))}")
bots = resp.json().get('result', [])
if isinstance(bots, list) and len(bots) > 0:
    for b in bots:
        msg = str(b.get('message','') or '')[:200]
        print(f"Bot {b['id']}: {b['name'][:45]} tm={b.get('text_match')}")
        print(f"  msg: {msg}")
        print()
else:
    print("No results. Trying direct read...")
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[62]],
            'kwargs':{'fields':['id','name','message','code']}
        }
    })
    print(f"read result: {json.dumps(resp2.json())[:1000]}")
