import requests, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s=requests.Session(); s.headers.update({'Content-Type':'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
def call(model,method,args,kwargs=None):
    r=s.post(f'https://latinbien.com/web/dataset/call_kw/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    j=r.json()
    if 'error' in j: print('   ERR', j['error'].get('message'), str(j['error'].get('data',''))[:200]); return None
    return j.get('result')
print('=== ultimos bot.log (connector 2, recientes) ===')
logs=call('acrux.chat.bot.log','search_read',[[]],{'fields':['id','text','bot_log','create_date'],'order':'id desc','limit':8})
for l in (logs or []):
    print(f"\n##### log #{l['id']} msg={l.get('text')!r} ({l.get('create_date')})")
    print(l.get('bot_log'))
