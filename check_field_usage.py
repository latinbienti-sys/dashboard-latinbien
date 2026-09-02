from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Read all cobranza bots (34, 40-47) + comercial bots (61, 62)
bids = [34, 40, 41, 42, 43, 44, 45, 46, 47, 61, 62]
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'search_read',
        'args':[[('id','in',bids)]],
        'kwargs':{'fields':['id','name','text_match','parent_id','code','body_whatsapp'], 'limit':30}
    }
})
bots = resp.json().get('result', [])
for b in sorted(bots, key=lambda x: x['id']):
    code = b.get('code','')
    pid = b.get('parent_id')
    parent = f"parent={pid[0]}" if isinstance(pid, list) else "ROOT"
    # detect which field it uses
    uses_conv_id = 'mess_id.conversation_id' in code or 'mess_id[' in code and 'conversation_id' in code
    uses_contact = 'mess_id.contact_id' in code or 'contact_id' in code
    uses_goto = "goto" in code
    has_ret = 'ret = env' in code
    print(f"Bot {b['id']}: {b['name'][:40]} tm={b.get('text_match')} {parent}")
    print(f"   conversation_id={'conversation_id' in code} | contact_id={'contact_id' in code} | ret={has_ret} | len={len(code)}")
    # print first 120 chars of code
    print(f"   code: {code[:120]!r}")
    print()
