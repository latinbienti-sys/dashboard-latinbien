from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Check total count of conversations
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_count', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_count',
        'args':[[]], 'kwargs':{}
    }
})
print(f"Total conversations: {resp.json().get('result', 'ERROR')}")

# Check if the user can see conversations at all - get just 3
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[]],
        'kwargs':{'fields':['id','number','connector_id','status','create_date'],
            'limit':5}
    }
})
convs = resp.json().get('result', [])
print(f"Visible conversations: {len(convs)}")
for c in convs:
    conn = c.get('connector_id')
    conn_name = f"conn_{conn[0]}" if conn else "?"
    print(f"  ID {c['id']}: {c['number']} conn={conn_name} status={c['status']} created={str(c.get('create_date',''))[:16]}")
