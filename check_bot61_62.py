from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Check bots 61, 62, 34, 45 - full details
for bid in [61, 62, 34, 45]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[bid]],
            'kwargs':{'fields':['id','name','active','connector_id','parent_id','text_match','sequence','bot_key','code','apply_from','apply_to','apply_weekday']}
        }
    })
    b = resp.json().get('result', [None])[0]
    if not b:
        print(f"Bot {bid}: NO ACCESS")
        continue
    print(f"=== Bot {bid}: {b['name']} ===")
    for k in ['active','connector_id','parent_id','text_match','sequence','bot_key','apply_from','apply_to','apply_weekday']:
        print(f"  {k}: {repr(b.get(k))}")
    code = b.get('code','')
    print(f"  code ({len(code)} chars): {code[:200]}")
    print()
