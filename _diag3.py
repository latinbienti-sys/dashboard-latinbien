import requests, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s=requests.Session(); s.headers.update({'Content-Type':'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
def call(model,method,args,kwargs=None):
    r=s.post(f'https://latinbien.com/web/dataset/call_kw/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    j=r.json()
    if 'error' in j: print('   ERR', j['error'].get('message'), str(j['error'].get('data',''))[:120])
    return j.get('result')
print('--- conversaciones conn 2 (sin active_bot_id) ---')
c=call('acrux.chat.conversation','search_read',[[('connector_id','=',2)]],{'fields':['id','number','status','last_event_date','message_count'],'order':'id desc','limit':30})
print('count:', len(c or []))
for x in (c or []):
    print(f"  #{x['id']} num={x.get('number')} status={x.get('status')} msgs={x.get('message_count')} last={x.get('last_event_date')}")
print('--- ultimo thread por conversacion ---')
acts=call('acrux.chat.conversation.activities','search_read',[[('ttype','=','bot_thread')]],{'fields':['id','conversation_id','rec_id','create_date'],'order':'id desc','limit':60})
from collections import defaultdict
last={}
for a in (acts or []):
    cid=a['conversation_id'][0] if isinstance(a['conversation_id'],list) else a['conversation_id']
    if cid not in last: last[cid]=(a['rec_id'], a['create_date'])
for cid,(rec,dt) in sorted(last.items()):
    print(f"  conv {cid}: ultimo thread rec_id={rec} ({dt})")
