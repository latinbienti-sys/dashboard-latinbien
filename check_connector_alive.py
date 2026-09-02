from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Simple test: get any conversation
print("Session OK, testing...")

# Simple test: get any conversation
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[],
        'fields':['id','number','connector_id','status'],
        'limit':5
    }
})
print(f"Status: {resp.status_code}")
result = resp.json().get('result')
if result is None:
    print("No result, checking error:", str(resp.json().get('error',''))[:300])
else:
    records = result.get('records', [])
    print(f"Conversations found: {len(records)}")
    for r in records:
        print(f"  {r}")

# Try call_kw  
print("\n--- Via call_kw ---")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[]],
        'kwargs':{'fields':['id','number','connector_id','status'],'limit':5}
    }
})
records = resp.json().get('result', [])
print(f"Conversations found: {len(records)}")
for r in records:
    print(f"  {r}")
