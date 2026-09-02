import requests, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s=requests.Session(); s.headers.update({'Content-Type':'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
def call(model,method,args,kwargs=None):
    r=s.post(f'https://latinbien.com/web/dataset/call_kw/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    j=r.json()
    if 'error' in j: print('   ERR', j['error'].get('message'), str(j['error'].get('data',''))[:120])
    return j.get('result')
for bid in [34,62,131,134]:
    b=call('acrux.chat.bot','read',[[bid]],{'fields':['id','name','bot_key','parent_id','child_ids','text_match','code']})
    if not b: print('no bot',bid); continue
    b=b[0]
    print(f"\n=== bot {bid} {b.get('name')} key={b.get('bot_key')} parent={b.get('parent_id')} hijos={b.get('child_ids')} tm={b.get('text_match')} ===")
    print((b.get('code') or '(sin codigo)')[:600])
