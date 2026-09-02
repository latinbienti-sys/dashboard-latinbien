from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Check message field and code of key commercial bots
for bid in [61, 62, 65, 66, 64, 63]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.bot','method':'read',
            'args':[[bid]],
            'kwargs':{'fields':['id','name','message','text_match','sequence','parent_id','code']}
        }
    })
    b = resp.json().get('result', [None])[0]
    if not b:
        print(f"Bot {bid}: NO ACCESS")
        continue
    msg = b.get('message') or ''
    print(f"=== Bot {bid}: {b['name']} ===")
    print(f"  text_match={b.get('text_match')} seq={b.get('sequence')} parent={b.get('parent_id')}")
    print(f"  MESSAGE ({len(msg)} chars): {str(msg)[:300]}")
    code = b.get('code','')
    print(f"  CODE ({len(code)} chars): {code[:150]}")
    print()
