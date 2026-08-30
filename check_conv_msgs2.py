import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Get recent messages for connector 2 conversations
conv_ids = [33146, 33148, 33140, 33147]

for cid in conv_ids:
    # Get messages using contact_id field
    resp = s.post('https://latinbien.com/web/dataset/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{
            'model':'acrux.chat.message',
            'domain':[('contact_id','=',cid)],
            'fields':['id','text','create_date','from_me'],
            'order':'create_date asc',
            'limit':20
        }
    })
    records = resp.json().get('result', {}).get('records', [])
    if records:
        print(f"=== Conv {cid} ({len(records)} messages) ===")
        for m in records:
            direction = ">>ENV" if m.get('from_me') else "<<REC"
            print(f"  [{m['create_date'][:19]}] {direction}: {str(m.get('text',''))[:200]}")
        print()
    else:
        # Try the call_kw method
        resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
            'jsonrpc':'2.0','method':'call',
            'params':{'model':'acrux.chat.message','method':'search_read',
                'args':[[('contact_id','=',cid)]],
                'kwargs':{'fields':['id','text','create_date','from_me'],
                    'order':'create_date asc',
                    'limit':20}
            }
        })
        records2 = resp2.json().get('result', [])
        if records2:
            print(f"=== Conv {cid} ({len(records2)} messages via call_kw) ===")
            for m in records2:
                direction = ">>ENV" if m.get('from_me') else "<<REC"
                print(f"  [{m['create_date'][:19]}] {direction}: {str(m.get('text',''))[:200]}")
            print()
        else:
            print(f"Conv {cid}: no messages or no access")
