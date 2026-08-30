import requests, json, sys, datetime
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

today = datetime.date.today().isoformat()

# Search all conversations the user CAN see, ordered by write_date desc
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[]],
        'kwargs':{'fields':['id','number','connector_id','status','active_bot_id','write_date'],
            'order':'write_date desc',
            'limit':20}
    }
})
convs = resp.json().get('result', [])
print(f"Total conversations accessible: {len(convs)}")
for c in convs:
    conn = c.get('connector_id')
    conn_name = f"conn_{conn[0]}" if conn else "?"
    active = c.get('active_bot_id')
    active_name = f'bot_{active[0]}' if active else 'NONE'
    print(f"  ID {c['id']}: {c['number']} conn={conn_name} status={c['status']} active={active_name} write={str(c.get('write_date',''))[:16]}")
    # Get messages for this conversation
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.message','method':'search_read',
            'args':[[('conversation_id', '=', c['id'])]],
            'kwargs':{'fields':['id','text','create_date','from_me'],
                'order':'create_date asc',
                'limit':10}
        }
    })
    msgs = resp2.json().get('result', [])
    if msgs:
        for m in msgs:
            direction = ">>ENV" if m.get('from_me') else "<<REC"
            print(f"    [{m['create_date'][:19]}] {direction}: {str(m.get('text',''))[:100]}")
    else:
        print(f"    (no messages visible)")
    print()
