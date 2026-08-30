import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Check who has access: what group does the API user belong to?
resp = s.post('https://latinbien.com/web/dataset/call_kw/res.users/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'res.users','method':'read',
        'args':[[102]], # our user
        'kwargs':{'fields':['id','name','login','groups_id']}
    }
})
print("API user:", json.dumps(resp.json().get('result', {}), default=str)[:2000])

# Check WhatsApp numbers via the ONLY accessible path
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[('connector_id','=',2)],
        'fields':['id','number','active_bot_id','status'],
        'limit':20
    }
})
records = resp.json().get('result', {}).get('records', [])
print(f"\nConversations on conn 2 ({len(records)}):")
active_bots_seen = set()
for r in records:
    active = r.get('active_bot_id')
    if isinstance(active, list):
        active_bots_seen.add(active[0])
    else:
        active_bots_seen.add(-1)

if active_bots_seen:
    print(f"Active bot IDs seen: {active_bots_seen}")

# Let me check: maybe the issue is that bot 61 was deactivated somehow?
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read',
        'args':[[61]],
        'kwargs':{'fields':['id','name','active','connector_id','parent_id']}
    }
})
b61 = resp.json().get('result', [None])[0]
print(f"\nBot 61 status: {json.dumps(b61, default=str)[:300]}")
