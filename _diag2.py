import requests, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s=requests.Session(); s.headers.update({'Content-Type':'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
def call(model,method,args,kwargs=None):
    r=s.post(f'https://latinbien.com/web/dataset/call_kw/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    j=r.json()
    if 'error' in j: print('   ERR', j['error'].get('message'), str(j['error'].get('data',''))[:150])
    return j.get('result')
print('--- 130 / 61 orden ---')
for bid in [130,61]:
    b=call('acrux.chat.bot','read',[[bid]],{'fields':['id','name','seq','sequence','parent_id','child_ids']})[0]
    print(f"bot {bid}: seq={b.get('seq')} sequence={b.get('sequence')} parent={b.get('parent_id')} hijos={b.get('child_ids')}")
print('--- conversaciones conn 2 ---')
c=call('acrux.chat.conversation','search_read',[[('connector_id','=',2)]],{'fields':['id','number','status','active_bot_id'],'order':'id desc','limit':20})
print('count convs:', len(c or []))
for x in (c or []):
    ab=x.get('active_bot_id'); abn=ab[1] if isinstance(ab,list) else ab
    print(f"  #{x['id']} num={x.get('number')} status={x.get('status')} active_bot={abn}")
print('--- activities (threads) conn 2 ---')
a=call('acrux.chat.conversation.activities','search_read',[[('ttype','=','bot_thread')]],{'fields':['id','conversation_id','rec_id'],'limit':20})
print('count threads:', len(a or []))
for x in (a or []):
    print('  thread rec_id=', x.get('rec_id'), 'conv=', x.get('conversation_id'))
