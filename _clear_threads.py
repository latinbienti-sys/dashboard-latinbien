import requests, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s=requests.Session(); s.headers.update({'Content-Type':'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
def call(model,method,args,kwargs=None):
    r=s.post(f'https://latinbien.com/web/dataset/call_kw/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    j=r.json()
    if 'error' in j: print('   ERR', j['error'].get('message'), str(j['error'].get('data',''))[:160]); return None
    return j.get('result')

# Todos los bots del conector 2 (comercial)
bot_ids = call('acrux.chat.bot','search',[[('connector_id','=',2)]],{})
print('bots conn2:', len(bot_ids or []), bot_ids)

# Actividades de thread en conn2
acts = call('acrux.chat.conversation.activities','search',[[('ttype','=','bot_thread'),('rec_id','in',bot_ids)]],{})
print('threads a limpiar (conn2):', len(acts or []))

if acts:
    ok = call('acrux.chat.conversation.activities','unlink',[acts],{})
    print('unlink resultado:', ok)

# Verificacion
rest = call('acrux.chat.conversation.activities','search_count',[[('ttype','=','bot_thread'),('rec_id','in',bot_ids)]],{})
print('threads restantes conn2:', rest)
