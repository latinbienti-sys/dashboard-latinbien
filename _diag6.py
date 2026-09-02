import requests, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s=requests.Session(); s.headers.update({'Content-Type':'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
def call(model,method,args,kwargs=None):
    r=s.post(f'https://latinbien.com/web/dataset/call_kw/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    j=r.json()
    if 'error' in j: print('   ERR', j['error'].get('message'), str(j['error'].get('data',''))[:200]); return None
    return j.get('result')
flds=['id','name','bot_key','parent_id','connector_id','text_match','active','apply_weekday','apply_from','apply_to','mute_minutes','seq','sequence','child_ids']
b=call('acrux.chat.bot','read',[[130]],{'fields':flds})[0]
for k in flds:
    v=b.get(k)
    if isinstance(v,list): v=v
    print(f"{k}: {v}")
print('--- bot 61 filtros ---')
b=call('acrux.chat.bot','read',[[61]],{'fields':flds})[0]
for k in flds:
    print(f"{k}: {b.get(k)}")
print('--- todos los ROOT bots (parent False) conn 2 ---')
roots=call('acrux.chat.bot','search_read',[[('parent_id','=',False),('connector_id','=',2)]],{'fields':['id','name','seq','sequence','text_match','connector_id','active']})
for r in (roots or []):
    print(r)
