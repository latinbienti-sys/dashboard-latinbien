from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# 1. Get ALL conversations for the test number (584147305385)
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[('number','=','584147305385')],
        'fields':['id','status','active_bot_id','connector_id','last_message_date','write_date'],
        'order':'write_date desc',
        'limit':5
    }
})
records = resp.json().get('result', {}).get('records', [])
print(f"Conversaciones para 584147305385 ({len(records)}):")
for r in records:
    active = r.get('active_bot_id')
    active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
    conn = r.get('connector_id')
    conn_name = f"conn_{conn[0]}" if isinstance(conn, list) else "?"
    print(f"  ID {r['id']}: status={r['status']} active={active_name} conn={conn_name}")

# 2. Get ALL conversations for the commercial number (584247035927)
print(f"\nConversaciones para 584247035927:")
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[('number','=','584247035927')],
        'fields':['id','status','active_bot_id','connector_id','last_message_date','write_date'],
        'order':'write_date desc',
        'limit':5
    }
})
records = resp.json().get('result', {}).get('records', [])
for r in records:
    active = r.get('active_bot_id')
    active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
    conn = r.get('connector_id')
    conn_name = f"conn_{conn[0]}" if isinstance(conn, list) else "?"
    print(f"  ID {r['id']}: status={r['status']} active={active_name} conn={conn_name}")

# 3. Check: What connector is being used when user writes to 584247035927?
# Let me search the MOST RECENT conversation
print(f"\nÚLTIMAS conversaciones en conector 2:")
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.conversation',
        'domain':[('connector_id','=',2)],
        'fields':['id','number','status','active_bot_id','last_message_date'],
        'order':'write_date desc',
        'limit':10
    }
})
records = resp.json().get('result', {}).get('records', [])
for r in records:
    active = r.get('active_bot_id')
    active_name = f"bot_{active[0]}" if isinstance(active, list) else "NONE"
    print(f"  ID {r['id']}: {r['number']} status={r['status']} active={active_name} last_msg={str(r.get('last_message_date',''))[:19]}")
