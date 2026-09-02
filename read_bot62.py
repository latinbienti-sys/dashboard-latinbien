import requests, json
s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read','args':[[62]],'kwargs':{'fields':['id','name','code']}}
})
b = resp.json()['result'][0]
print(f"Bot 62: {b['name']}")
print(b['code'])
