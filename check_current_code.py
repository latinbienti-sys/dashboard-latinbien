from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read','args':[[61,62]],'kwargs':{'fields':['id','name','code']}}
})
for b in resp.json()['result']:
    c = b.get('code','')
    name = b['name']
    bid = b['id']
    print(f'=== Bot {bid}: {name} ===')
    print(c[:300])
    print('...' if len(c)>300 else '')
    print()
