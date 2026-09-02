from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# All connector-2 bots, check usage of conversation_id / active_bot_id
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'search_read',
        'args':[[('connector_id','=',2)]],
        'kwargs':{'fields':['id','name','text_match','parent_id','code'], 'limit':80}
    }
})
bots = resp.json().get('result', [])
print(f"=== Uso de conversation_id / active_bot_id en bots conector 2 ({len(bots)}) ===")
for b in sorted(bots, key=lambda x: x['id']):
    code = b.get('code','')
    uses_conv = 'conversation_id' in code
    uses_act = 'active_bot_id' in code
    if uses_conv or uses_act:
        print(f"Bot {b['id']}: {b['name'][:40]} tm={b.get('text_match')} parent={b.get('parent_id')}")
        if uses_conv:
            print(f"   conversation_id: {[l.strip()[:90] for l in code.split(chr(10)) if 'conversation_id' in l][:3]}")
        if uses_act:
            print(f"   active_bot_id:    {[l.strip()[:90] for l in code.split(chr(10)) if 'active_bot_id' in l][:3]}")
        print()
