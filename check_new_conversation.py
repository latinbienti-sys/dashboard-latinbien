import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Check the 'new' conversation details - what does it have for active_bot_id?
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'read',
        'args':[[33152]],
        'kwargs':{'fields':['id','number','connector_id','status','active_bot_id','last_message_date','create_date']}
    }
})
print("Conversation 33152:", json.dumps(resp.json().get('result', [{}])[0], default=str)[:500])

# Now try to find which bots are linked to WhatsApp numbers
# Maybe we can access waba.number through the conversation
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.message','method':'search_read',
        'args':[[('contact_id','=',33152)]],
        'kwargs':{'fields':['id','text','from_me','create_date'],
            'order':'create_date asc',
            'limit':10}
    }
})
print(f"\nMessages in conv 33152:")
for m in resp.json().get('result', []):
    direction = ">>" if m.get('from_me') else "<<"
    print(f"  [{m['create_date'][:19]}] {direction}: {str(m.get('text',''))[:100]}")

# Check if the connector has a default bot set (maybe via context)
print("\n\n--- Checking bot assignment via connector 2 ---")
# Look at any conversation that IS working on connector 2 (e.g., 33155 or 33153)
for cid in [33155, 33153, 33154]:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.conversation','method':'read',
            'args':[[cid]],
            'kwargs':{'fields':['id','number','connector_id','status','active_bot_id']}
        }
    })
    conv = resp.json().get('result', [None])[0]
    if conv:
        active = conv.get('active_bot_id')
        active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
        print(f"  Conv {cid}: {conv['number']} status={conv['status']} active={active_name}")
