import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# 1) Get fields of acrux.chat.conversation to know correct field names
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/fields_get', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'fields_get',
        'args':[[]],'kwargs':{'attributes':['string','type','relation']}
    }
})
fields = resp.json().get('result', {})
if not fields:
    print("Error fields conversation:", str(resp.json())[:400])
else:
    interesting = ['id','name','number','status','active_bot_id','connector_id','bot_id','last_message','message_ids','last_active','blocked','channel']
    print("Conversation fields (interesting):")
    for f in interesting:
        if f in fields:
            print(f"  {f}: {fields[f].get('string')} ({fields[f].get('type')}) rel={fields[f].get('relation','')}")

# 2) Search test conversation 584147305385
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[('number','ilike','584147305385')]],
        'kwargs':{'fields':['id','number','status','active_bot_id','bot_id','connector_id','last_active','blocked'],
            'limit':5}
    }
})
result = resp.json().get('result')
print(f"\nSearch conversation result: {type(result)}")
print(str(result)[:1500])
if result is None:
    print("Error:", str(resp.json().get('error',{}).get('data',{}).get('message',''))[:300])

# 3) Search test conversation 584247035927 (commercial number)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[('number','ilike','584247035927')]],
        'kwargs':{'fields':['id','number','status','active_bot_id','bot_id','connector_id','last_active','blocked'],
            'limit':5}
    }
})
result = resp.json().get('result')
print(f"\nSearch comercial conv result: {type(result)}")
print(str(result)[:1500])
if result is None:
    print("Error:", str(resp.json().get('error',{}).get('data',{}).get('message',''))[:300])
