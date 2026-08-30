import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Check recent conversations on connector 2
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[('connector_id', '=', 2)]],
        'kwargs':{'fields':['id','number','status','active_bot_id','last_message_date','write_date'],
            'order':'write_date desc',
            'limit':5}
    }
})
print("Conversaciones recientes en conector 2:")
for c in resp.json().get('result', []):
    active = c.get('active_bot_id')
    active_name = f'bot_{active[0]}' if active else 'NONE'
    print(f"  ID {c['id']}: {c['number']} status={c['status']} active={active_name}")
