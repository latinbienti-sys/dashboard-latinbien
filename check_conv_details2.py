from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Get conversation 33146 details via search_read
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[('id', 'in', [33146, 33148, 33140])]],
        'kwargs':{'fields':['id','number','connector_id','status','active_bot_id','last_message_date'],
            'limit':10}
    }
})
convs = resp.json().get('result', [])
print(f"Found {len(convs)} conversations")
for c in convs:
    active = c.get('active_bot_id')
    active_name = f'bot_{active[0]}' if active else 'NONE'
    print(f"  ID {c['id']}: {c['number']} status={c['status']} active={active_name} last_msg={str(c.get('last_message_date',''))[:16]}")
    print()

# Get messages for these conversations
for cid_info in convs:
    cid = cid_info['id']
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.message','method':'search_read',
            'args':[[('conversation_id', '=', cid)]],
            'kwargs':{'fields':['id','text','create_date','from_me'],
                'order':'create_date asc',
                'limit':20}
        }
    })
    msgs = resp.json().get('result', [])
    if msgs:
        print(f"  Mensajes para conv {cid} ({cid_info['number']}):")
        for m in msgs:
            direction = ">>ENV" if m.get('from_me') else "<<REC"
            print(f"    [{m['create_date'][:19]}] {direction}: {str(m.get('text',''))[:150]}")
    else:
        print(f"  No messages for conv {cid}")
    print()
