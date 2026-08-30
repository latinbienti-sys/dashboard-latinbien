# -*- coding: utf-8 -*-
# ENCIENDE/APAGA el catcher de moto cambiando el campo 'active' de los bots 130/131/134.
# Uso:  python toggle_moto.py on   |   python toggle_moto.py off
import requests, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s=requests.Session(); s.headers.update({'Content-Type':'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
def call(model,method,args,kwargs=None):
    r=s.post(f'https://latinbien.com/web/dataset/call_kw/{model}/{method}', json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args,'kwargs':kwargs or {}}})
    return r.json().get('result')

mode = (sys.argv[1].lower() if len(sys.argv)>1 else 'on')
if mode not in ('on','off'):
    print('Usa: python toggle_moto.py on   o   python toggle_moto.py off'); sys.exit(1)
active = (mode=='on')
ids=[130,131,134]
call('acrux.chat.bot','write',[ids,{'active':active}])
res=call('acrux.chat.bot','read',[ids],{'fields':['id','name','active']})
print(f"Catcher de moto {'ENCENDIDO (activo)' if active else 'APAGADO (inactivo)'}:")
for b in res:
    print(f"  [{b['id']}] {b['name']} active={b['active']}")
print('\nEncendido: pregunta moto en el 1er mensaje. Apagado: flujo comercial normal (bot 61).')
