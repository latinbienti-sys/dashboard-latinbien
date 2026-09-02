from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Get conversations for the test number
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[('number','=','584147305385')],
        'fields':['id','status','active_bot_id','last_message_date','write_date'],
        'order':'write_date desc',
        'limit':5
    }
})
records = resp.json().get('result', {}).get('records', [])
print(f"Conversaciones para 584147305385:")
for r in records:
    active = r.get('active_bot_id')
    active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
    print(f"  ID {r['id']}: status={r['status']} active={active_name}")

# Get messages for the most recent one
if records:
    cid = records[0]['id']
    print(f"\nMensajes en conv {cid}:")
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
        'jsonrpc':'2.0','method':'call',
        'params':{'model':'acrux.chat.message','method':'search_read',
            'args':[[('contact_id','=',cid)]],
            'kwargs':{'fields':['id','text','from_me','create_date'],
                'order':'create_date asc',
                'limit':20}
        }
    })
    for m in resp.json().get('result', []):
        direction = ">>ENV" if m.get('from_me') else "<<REC"
        print(f"  [{m['create_date'][:19]}] {direction}: {str(m.get('text',''))[:120]}")

# Check ALL recent conversations on connector 2
print("\n\nÚltimas conversaciones en conector 2:")
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[('connector_id','=',2)],
        'fields':['id','number','status','active_bot_id','write_date'],
        'order':'write_date desc',
        'limit':15
    }
})
records = resp.json().get('result', {}).get('records', [])
for r in records:
    active = r.get('active_bot_id')
    active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
    print(f"  ID {r['id']}: {r['number']} status={r['status']} active={active_name} write={str(r.get('write_date',''))[:19]}")
