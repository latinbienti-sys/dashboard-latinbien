from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Focus on recent connector 2 conversations
conv_ids = [33146, 33148, 33140]
for cid in conv_ids:
    print(f"=== Conversation {cid} ===")
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.conversation','method':'read','args':[[cid]],
            'kwargs':{'fields':['id','number','connector_id','status','active_bot_id','last_message_date']}
        }
    })
    c = resp.json()['result'][0]
    active = c.get('active_bot_id')
    active_name = f'bot_{active[0]}' if active else 'NONE'
    print(f"  number={c['number']} status={c['status']} active={active_name}")
    
    # Get messages
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.message','method':'search_read',
            'args':[[('conversation_id', '=', cid)]],
            'kwargs':{'fields':['id','text','create_date','from_me'],
                'order':'create_date asc',
                'limit':30}
        }
    })
    msgs = resp.json().get('result', [])
    for m in msgs:
        direction = "ENVIADO>>" if m.get('from_me') else "<<RECIBIDO"
        print(f"  [{m['create_date'][:19]}] {direction}: {str(m.get('text',''))[:150]}")
    print()
