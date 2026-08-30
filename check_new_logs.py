import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get MAX log ID
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['id'], 'domain': [], 'limit': 1, 'order': 'id desc'}
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    max_id = records[0]['id'] if records else 0
    print(f'Max log ID: {max_id}')
    
    # Now search for cobranza logs near max_id
    if max_id > 25761:
        resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
                'args': [],
                'kwargs': {
                    'fields': ['id', 'bot_log', 'connector_id'],
                    'domain': [['id', '>', 25761], ['connector_id', '=', 17]],
                    'limit': 10,
                    'order': 'id asc'
                }
            }
        })
        r2 = resp2.json()
        if 'result' in r2:
            records2 = r2['result']
            if isinstance(records2, dict): records2 = records2.get('records', [])
            if records2:
                print(f'New cobranza logs since 25761: {len(records2)}')
                for log in records2:
                    lid = log['id']
                    logtxt = str(log.get('bot_log', ''))[:200]
                    print(f'  Log {lid}: {logtxt}')
            else:
                print('No new cobranza logs found')
        else:
            print('Error:', r2.get('error', {}))
    else:
        print('No new logs since 25761')
