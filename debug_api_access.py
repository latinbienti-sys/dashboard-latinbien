import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
r = s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
print("uid:", r.json().get('result', {}).get('uid'))

# Method 1: flat /web/dataset/search_read - check raw response
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[],
        'fields':['id','number','status'],
        'order':'write_date desc',
        'limit':5
    }
})
print("\n[Flat search_read] full response:", json.dumps(resp.json())[:800])

# Method 2: call_kw search_count
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_count', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_count',
        'args':[[]],'kwargs':{}
    }
})
print("\n[call_kw search_count] result:", resp.json().get('result'), "err:", str(resp.json().get('error',{}).get('data',{}).get('message',''))[:200])

# Method 3: call_kw search_read with no domain
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[]],
        'kwargs':{'fields':['id','number','status'], 'limit':5}
    }
})
print("\n[call_kw search_read] result:", json.dumps(resp.json())[:800])

# Method 4: check other models work at all - res.partner
resp = s.post('https://latinbien.com/web/dataset/call_kw/res.partner/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'res.partner','method':'search_read',
        'args':[[('vat','=','V15921224')]],
        'kwargs':{'fields':['id','name','vat'], 'limit':3}
    }
})
print("\n[res.partner search_read] result:", json.dumps(resp.json())[:800])
