import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Read conversation 33152 details - what fields exist that relate to bot state?
# First list fields visible via read (may include active_bot_id if it's a real field)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'read',
        'args':[[33152]],
        'kwargs':{'fields':['id','number','status','name','connector_id','last_message_date','write_date','create_date','agent_id','stage_id','team_id','note','tmp_agent_id','sale_order_id']}
    }
})
print("Conv 33152:", json.dumps(resp.json().get('result'), indent=1, ensure_ascii=False)[:1200])

# Try to read 'active_bot_id' explicitly on conversation
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'read',
        'args':[[33152]],
        'kwargs':{'fields':['id','number','active_bot_id']}
    }
})
print("\nTry active_bot_id:", json.dumps(resp.json())[:500])

# Get messages for conversation 33152
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.message','method':'search_read',
        'args':[[('contact_id','=',33152)]],
        'kwargs':{'fields':['id','text','from_me','create_date','date_message','event','error_msg'],
            'order':'create_date asc',
            'limit':30}
    }
})
msgs = resp.json().get('result', [])
print(f"\nMensajes en conv 33152 ({len(msgs)}):")
for m in msgs:
    direction = ">>ENV" if m.get('from_me') else "<<REC"
    ev = m.get('event') or ''
    err = m.get('error_msg') or ''
    print(f"  [{m['create_date'][:19]}] {direction} {ev} {err}: {str(m.get('text',''))[:180]}")
