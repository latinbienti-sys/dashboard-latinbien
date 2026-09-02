from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

today = datetime.date.today().isoformat()

# Check ALL recent conversations across all connectors
print(f"=== All conversations today ({today}) ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[('create_date', '>=', today)]],
        'kwargs':{'fields':['id','number','connector_id','status','active_bot_id','last_message_date','write_date'],
            'order':'write_date desc',
            'limit':20}
    }
})
convs = resp.json().get('result', [])
if convs:
    for c in convs:
        conn = c.get('connector_id')
        conn_name = f"conn_{conn[0]}" if conn else "?"
        active = c.get('active_bot_id')
        active_name = f'bot_{active[0]}' if active else 'NONE'
        print(f"  ID {c['id']}: {c['number']} conn={conn_name} status={c['status']} active={active_name} last_msg={str(c.get('last_message_date',''))[:16]}")
else:
    print("No conversations today")

# Also check ALL messages today
print(f"\n=== All messages today ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.message','method':'search_read',
        'args':[[('create_date', '>=', today)]],
        'kwargs':{'fields':['id','text','create_date','from_me','conversation_id'],
            'order':'create_date desc',
            'limit':30}
    }
})
msgs = resp.json().get('result', [])
if msgs:
    for m in msgs:
        conv = m.get('conversation_id')
        conv_name = f"conv_{conv[0]}" if conv else "?"
        direction = ">>" if m.get('from_me') else "<<"
        print(f"  [{m['create_date'][:19]}] {direction} {conv_name}: {str(m.get('text',''))[:120]}")
else:
    print("No messages today")
