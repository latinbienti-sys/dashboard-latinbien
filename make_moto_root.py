# -*- coding: utf-8 -*-
# PROMUEVE el catcher de moto a BOT RAIZ (parent_id=False) con sequence=1 (menor que 61 que es 38),
# asi se evalua en el PRIMER mensaje del cliente y "pasa algo" de inmediato.
# Mantiene su codigo validado. 131/134 siguen como hijos. Es toggleable via campo 'active'.
import requests, sys, json
sys.stdout = sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1) if False else sys.stdout
import io, sys as _sys
_sys.stdout = io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')
s = requests.Session(); s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
API='https://latinbien.com/web/dataset/call_kw'
def call(model,method,args,kwargs=None):
    r=s.post(f'{API}/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    j=r.json()
    if 'error' in j: print('   !! ERROR', j['error'].get('message'), str(j['error'].get('data',''))[:200])
    return j.get('result')

# 1) Leer codigo actual de 130 para reutilizarlo
b130=call('acrux.chat.bot','read',[[130]],{'fields':['id','name','code','bot_key','text_match','sequence','parent_id','active']})[0]
print('130 actual: parent=',b130['parent_id'],'seq=',b130['sequence'],'key=',b130['bot_key'])

# 2) Convertir 130 en raiz (parent_id=False) y seq=1 (antes de 61 que es 38)
call('acrux.chat.bot','write',[[130],{
    'parent_id': False,
    'sequence': 1,
    'text_match': False,
    'bot_key': '#MOTO_CATCHER_61',
    'code': b130['code'],
    'active': True,
}])
print('130 promovido a RAIZ (parent_id=False), seq=1')

# 3) Verificar que 131 sigue hijo de 130 y 134 hijo de 131
tree=call('acrux.chat.bot','read',[[130,131,134]],{'fields':['id','name','parent_id','bot_key','child_ids','sequence','active']})
print('\n=== Arbol moto (130 raiz) ===')
for b in tree:
    print(f"  [{b['id']}] {b['name']} parent={b['parent_id'][0] if b['parent_id'] else None} key={b['bot_key']} hijos={b['child_ids']} seq={b['sequence']} active={b['active']}")

# 4) Verificar que 61 sigue raiz y ahora SIN 130 entre sus hijos
b61=call('acrux.chat.bot','read',[[61]],{'fields':['id','parent_id','sequence','child_ids']})[0]
print('\n61: parent=',b61['parent_id'],'seq=',b61['sequence'],'hijos=',b61['child_ids'])
print('\nOK: moto catcher es raiz independiente, se evalua en el 1er mensaje. Toggle: poner active=False en 130/131/134 para apagar.')
