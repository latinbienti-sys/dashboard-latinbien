import requests, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s=requests.Session(); s.headers.update({'Content-Type':'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
def call(model,method,args,kwargs=None):
    r=s.post(f'https://latinbien.com/web/dataset/call_kw/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    j=r.json()
    if 'error' in j: print('   ERR', j['error'].get('message'), str(j['error'].get('data',''))[:200]); return None
    return j.get('result')
print('=== ASESOR bots 97-100 (notify pattern) ===')
for bid in [97,98,99,100]:
    b=call('acrux.chat.bot','read',[[bid]],{'fields':['id','name','code']})
    if not b: continue
    b=b[0]
    print(f"\n--- bot {bid} {b['name']} ---")
    print(b['code'] or '(sin codigo)')
print('\n=== CURRENT moto bots 130/131/134 full code ===')
for bid in [130,131,134]:
    b=call('acrux.chat.bot','read',[[bid]],{'fields':['id','name','code']})
    if not b: continue
    b=b[0]
    print(f"\n--- bot {bid} {b['name']} ---")
    print(b['code'] or '(sin codigo)')
