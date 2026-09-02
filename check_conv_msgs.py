from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Look at connector 2 conversations - get messages for each
conv_ids = [33146, 33148, 33140, 33147, 10538, 7405, 21682]
for cid in conv_ids:
    # Get conversation details
    resp = s.post('https://latinbien.com/web/dataset/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{
            'model':'acrux.chat.conversation',
            'domain':[('id','=',cid)],
            'fields':['id','number','status','active_bot_id','write_date','create_date'],
            'limit':1
        }
    })
    records = resp.json().get('result', {}).get('records', [])
    if not records:
        continue
    c = records[0]
    active = c.get('active_bot_id')
    active_name = f'bot_{active[0]}' if active else 'NONE'
    print(f"=== Conv {cid}: {c['number']} status={c['status']} active={active_name} ===")
    
    # Get messages
    resp = s.post('https://latinbien.com/web/dataset/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{
            'model':'acrux.chat.message',
            'domain':[('conversation_id','=',cid)],
            'fields':['id','text','create_date','from_me'],
            'order':'create_date asc',
            'limit':20
        }
    })
    msgs = resp.json().get('result', {}).get('records', [])
    for m in msgs:
        direction = ">>ENV" if m.get('from_me') else "<<REC"
        print(f"  [{m['create_date'][:19]}] {direction}: {str(m.get('text',''))[:200]}")
    print()
