from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Get latest state of conversation 33140
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'read',
        'args':[[33140]],
        'kwargs':{'fields':['id','number','connector_id','status','active_bot_id','last_message_date','write_date']}
    }
})
conv = resp.json().get('result', [None])[0]
if conv:
    active = conv.get('active_bot_id')
    active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
    print(f"Conv 33140: status={conv['status']} active={active_name}")
else:
    print("No access to conv 33140")

# Get ALL messages for conv 33140
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.message','method':'search_read',
        'args':[[('contact_id','=',33140)]],
        'kwargs':{'fields':['id','text','create_date','from_me'],
            'order':'create_date desc',
            'limit':50}
    }
})
msgs = resp.json().get('result', [])
print(f"\nTotal mensajes: {len(msgs)}")
for m in reversed(msgs):
    direction = ">>ENV" if m.get('from_me') else "<<REC"
    print(f"  [{m['create_date'][:19]}] {direction}: {str(m.get('text',''))[:120]}")
